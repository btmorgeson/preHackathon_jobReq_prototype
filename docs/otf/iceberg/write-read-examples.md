# Iceberg Write/Read Examples (Spark)

## Create Namespace and Table
```bash
docker exec -it spark-iceberg spark-sql \
  --conf spark.sql.catalog.demo=org.apache.iceberg.spark.SparkCatalog \
  --conf spark.sql.catalog.demo.type=rest \
  --conf spark.sql.catalog.demo.uri=http://iceberg-rest:8181 \
  --conf spark.sql.catalog.demo.warehouse=s3://warehouse/ \
  --conf spark.sql.catalog.demo.io-impl=org.apache.iceberg.aws.s3.S3FileIO \
  --conf spark.sql.catalog.demo.s3.endpoint=http://minio:9000 \
  --conf spark.sql.catalog.demo.s3.path-style-access=true \
  -e "
  CREATE NAMESPACE IF NOT EXISTS demo;
  CREATE TABLE IF NOT EXISTS demo.postings (
    posting_id string,
    title string,
    summary string,
    source_system string,
    source_id string,
    stable_id string,
    version string,
    ingested_at timestamp
  ) USING iceberg
  PARTITIONED BY (days(ingested_at));
  "
```

## Insert Sample Rows
```bash
docker exec -it spark-iceberg spark-sql \
  --conf spark.sql.catalog.demo=org.apache.iceberg.spark.SparkCatalog \
  --conf spark.sql.catalog.demo.type=rest \
  --conf spark.sql.catalog.demo.uri=http://iceberg-rest:8181 \
  --conf spark.sql.catalog.demo.warehouse=s3://warehouse/ \
  --conf spark.sql.catalog.demo.io-impl=org.apache.iceberg.aws.s3.S3FileIO \
  --conf spark.sql.catalog.demo.s3.endpoint=http://minio:9000 \
  --conf spark.sql.catalog.demo.s3.path-style-access=true \
  -e "
  INSERT INTO demo.postings VALUES
  ('p1','Data Engineer','Build ETL','usajobs','111','st_p1','2026-03-03', current_timestamp()),
  ('p2','ML Engineer','Build retrieval systems','usajobs','222','st_p2','2026-03-03', current_timestamp());
  SELECT * FROM demo.postings;
  "
```

## Inspect Snapshots
```bash
docker exec -it spark-iceberg spark-sql \
  --conf spark.sql.catalog.demo=org.apache.iceberg.spark.SparkCatalog \
  --conf spark.sql.catalog.demo.type=rest \
  --conf spark.sql.catalog.demo.uri=http://iceberg-rest:8181 \
  --conf spark.sql.catalog.demo.warehouse=s3://warehouse/ \
  --conf spark.sql.catalog.demo.io-impl=org.apache.iceberg.aws.s3.S3FileIO \
  --conf spark.sql.catalog.demo.s3.endpoint=http://minio:9000 \
  --conf spark.sql.catalog.demo.s3.path-style-access=true \
  -e "SELECT * FROM demo.postings.snapshots;"
```
