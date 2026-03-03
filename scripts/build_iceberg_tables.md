# Build Iceberg Tables

## Goal
Create Iceberg namespace and tables on local REST catalog + MinIO.

## Start Services
```bash
docker compose up -d minio iceberg-rest spark
```

## Create Bucket
```bash
docker run --rm --network prototype-pipeline_pipeline_net minio/mc \
  sh -c "mc alias set local http://minio:9000 minioadmin minioadmin123 && mc mb -p local/warehouse"
```

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
  ) USING iceberg PARTITIONED BY (days(ingested_at));
  "
```

## Verify
```bash
docker exec -it spark-iceberg spark-sql \
  --conf spark.sql.catalog.demo=org.apache.iceberg.spark.SparkCatalog \
  --conf spark.sql.catalog.demo.type=rest \
  --conf spark.sql.catalog.demo.uri=http://iceberg-rest:8181 \
  --conf spark.sql.catalog.demo.warehouse=s3://warehouse/ \
  --conf spark.sql.catalog.demo.io-impl=org.apache.iceberg.aws.s3.S3FileIO \
  --conf spark.sql.catalog.demo.s3.endpoint=http://minio:9000 \
  --conf spark.sql.catalog.demo.s3.path-style-access=true \
  -e "SHOW TABLES IN demo;"
```
