param(
  [Parameter(Mandatory = $true)]
  [ValidateSet("setup", "pipeline", "api", "frontend", "smoke", "vagrant-up", "vagrant-reset")]
  [string]$Task
)

switch ($Task) {
  "setup" {
    python scripts/validate_env.py --profile pipeline
  }
  "pipeline" {
    python scripts/run_pipeline.py
  }
  "api" {
    python scripts/validate_env.py --profile api
    uvicorn src.api.main:app --reload --port 8000
  }
  "frontend" {
    Set-Location frontend
    npm.cmd run dev
  }
  "smoke" {
    python scripts/06_smoke_test.py
  }
  "vagrant-up" {
    vagrant up
  }
  "vagrant-reset" {
    vagrant ssh -c "bash /workspace/scripts/vagrant/reset_and_import.sh"
  }
}
