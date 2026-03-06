import { expect, Page, test } from "@playwright/test";

interface SearchCandidate {
  person_stable_id: string;
  name: string;
  current_title: string;
  composite_score: number;
  skill_score: number;
  role_score: number;
  experience_score: number;
  evidence: string;
  matched_skills: string[];
}

function buildReqCandidates(): SearchCandidate[] {
  return [
    {
      person_stable_id: "person-req-1",
      name: "Avery Chen",
      current_title: "Senior Software Engineer",
      composite_score: 0.94,
      skill_score: 1.0,
      role_score: 0.91,
      experience_score: 0.89,
      evidence:
        "Strong Python and ETL delivery with recent Kubernetes workload ownership and cross-team communication.",
      matched_skills: ["Python", "ETL Pipeline Development", "Kubernetes", "Stakeholder Management"],
    },
    {
      person_stable_id: "person-req-2",
      name: "Jordan Patel",
      current_title: "Data Platform Engineer",
      composite_score: 0.87,
      skill_score: 0.86,
      role_score: 0.9,
      experience_score: 0.84,
      evidence:
        "Consistent ownership of data platform modernization and agile delivery across enterprise teams.",
      matched_skills: ["Python", "Agile", "Database Design"],
    },
    {
      person_stable_id: "person-req-3",
      name: "Riley Morgan",
      current_title: "Cloud Integration Engineer",
      composite_score: 0.78,
      skill_score: 0.74,
      role_score: 0.79,
      experience_score: 0.81,
      evidence:
        "Good alignment on Kubernetes and ETL, with moderate role fit and solid tenure in adjacent teams.",
      matched_skills: ["Kubernetes", "ETL Pipeline Development"],
    },
  ];
}

function buildDescriptionCandidates(): SearchCandidate[] {
  return [
    {
      person_stable_id: "person-desc-1",
      name: "Taylor Nguyen",
      current_title: "Principal Data Engineer",
      composite_score: 0.97,
      skill_score: 1.0,
      role_score: 0.96,
      experience_score: 0.95,
      evidence:
        "Excellent alignment with Python, ETL, Kubernetes, and SQL modeling requirements from the description workflow.",
      matched_skills: ["Python", "ETL", "Kubernetes", "SQL data modeling", "stakeholder communication"],
    },
    {
      person_stable_id: "person-desc-2",
      name: "Morgan Lee",
      current_title: "Data Engineering Manager",
      composite_score: 0.83,
      skill_score: 0.84,
      role_score: 0.8,
      experience_score: 0.85,
      evidence:
        "Strong stakeholder leadership with solid architecture depth; slightly less hands-on recent coding exposure.",
      matched_skills: ["stakeholder communication", "SQL data modeling", "Python"],
    },
  ];
}

async function mockBackend(page: Page) {
  await page.route("**/api/postings/**", async (route) => {
    await page.waitForTimeout(120);
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        stable_id: "posting-req-001",
        req_number: "REQ-001",
        title: "Software Engineer II",
        description: "Enterprise software development role.",
        required_skills: [
          "ETL Pipeline Development",
          "Python",
          "Agile",
          "Stakeholder Management",
          "Kubernetes",
        ],
        desired_skills: ["Technical Writing", "Database Design", "C#", "Node.js"],
      }),
    });
  });

  await page.route("**/api/extract-skills", async (route) => {
    await page.waitForTimeout(300);
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        required_skills: [
          "Python",
          "ETL",
          "Kubernetes",
          "stakeholder communication",
          "SQL data modeling",
        ],
        desired_skills: [],
      }),
    });
  });

  await page.route("**/api/search", async (route) => {
    const payload = route.request().postDataJSON() as Record<string, unknown>;
    const usingReqFlow = typeof payload.req_number === "string" && payload.req_number.length > 0;
    const candidates = usingReqFlow ? buildReqCandidates() : buildDescriptionCandidates();
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        request_id: usingReqFlow ? "req-mock-request-001" : "desc-mock-request-001",
        candidates,
        query_skills_used: [],
        timings_ms: {
          request_total: 325.7,
          scoring: 200.2,
          retrieval: 111.1,
        },
      }),
    });
  });
}

test.beforeEach(async ({ page }) => {
  await mockBackend(page);
});

test("req-number flow renders modern UI and interactive results", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Job Req Candidate Ranker" })).toBeVisible();

  const bodyBackgroundImage = await page.evaluate(() => getComputedStyle(document.body).backgroundImage);
  expect(bodyBackgroundImage).toContain("radial-gradient");

  await page.getByPlaceholder("e.g. REQ-001").fill("REQ-001");
  await page.getByRole("button", { name: "Load Req" }).click();

  await expect(page.getByText("Loaded context:")).toBeVisible();
  await page.getByRole("button", { name: "Find Candidates" }).click();

  await expect(
    page.getByText("3 candidates found. Select a row to inspect detailed evidence."),
  ).toBeVisible();
  await expect(page.getByText("SUCCESS")).toBeVisible();
  await expect(page.getByText("5 / 4")).toBeVisible();

  const firstRow = page.locator("tbody tr").first();
  await firstRow.click();
  await expect(page.getByText("Evidence").first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Avery Chen" })).toBeVisible();

  const compositeHeader = page.getByRole("columnheader", { name: /Composite/ });
  const firstCompositeBefore = await page.locator("tbody tr").first().locator("td").nth(3).textContent();
  await compositeHeader.click();
  const firstCompositeAfterSort = await page.locator("tbody tr").first().locator("td").nth(3).textContent();
  await compositeHeader.click();
  const firstCompositeAfterSecondSort = await page.locator("tbody tr").first().locator("td").nth(3).textContent();

  expect(new Set([firstCompositeBefore, firstCompositeAfterSort, firstCompositeAfterSecondSort]).size).toBeGreaterThan(1);
});

test("description flow enforces extraction gating and keeps summary consistent", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Role Description" }).click();

  await page
    .getByPlaceholder("Paste the job description text here...")
    .fill(
      "Senior data engineer with Python, ETL, Kubernetes, stakeholder communication, and SQL data modeling experience.",
    );

  await page.getByRole("button", { name: "Extract Skills" }).click();

  const submitButton = page.getByRole("button", { name: /Wait for skill sync|Find Candidates/ });
  await expect(submitButton).toBeDisabled();
  await expect(submitButton).toContainText("Wait for skill sync");

  await expect(page.getByRole("button", { name: "Find Candidates" })).toBeEnabled();
  await expect(page.getByRole("button", { name: /^Remove / })).toHaveCount(5);

  await page.getByRole("button", { name: "Find Candidates" }).click();

  await expect(
    page.getByText("2 candidates found. Select a row to inspect detailed evidence."),
  ).toBeVisible();
  await expect(page.getByText("5 / 0")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Taylor Nguyen" })).toBeVisible();
});

test.describe("mobile viewport", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test("results table remains usable with horizontal scroll", async ({ page }) => {
    await page.goto("/");
    await page.getByPlaceholder("e.g. REQ-001").fill("REQ-001");
    await page.getByRole("button", { name: "Load Req" }).click();
    await page.getByRole("button", { name: "Find Candidates" }).click();

    await expect(
      page.getByText("3 candidates found. Select a row to inspect detailed evidence."),
    ).toBeVisible();

    const scrollInfo = await page.evaluate(() => {
      const table = document.querySelector("table");
      const scroller = table?.parentElement;
      if (!table || !scroller) {
        return null;
      }
      const before = scroller.scrollLeft;
      scroller.scrollLeft = 220;
      const after = scroller.scrollLeft;
      return {
        before,
        after,
        clientWidth: scroller.clientWidth,
        scrollWidth: scroller.scrollWidth,
      };
    });

    expect(scrollInfo).not.toBeNull();
    expect(scrollInfo?.scrollWidth).toBeGreaterThan(scrollInfo?.clientWidth ?? 0);
    expect(scrollInfo?.after).toBeGreaterThan(scrollInfo?.before ?? 0);
  });
});
