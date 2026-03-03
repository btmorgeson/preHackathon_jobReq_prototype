# Local Lakehouse with MinIO + REST Catalog

## Stack
- MinIO object storage (`minio:9000`)
- Iceberg REST catalog (`iceberg-rest:8181`)
- Spark runtime container (`spark-iceberg`)

## Start Services
```bash
docker compose up -d minio iceberg-rest spark
```

## Create MinIO Bucket
```bash
docker run --rm --network prototype-pipeline_pipeline_net \
  minio/mc \
  sh -c "mc alias set local http://minio:9000 minioadmin minioadmin123 && mc mb -p local/warehouse"
```

## Spark Session Setup
Use these Spark catalog properties (REST catalog):
```text
spark.sql.catalog.demo=org.apache.iceberg.spark.SparkCatalog
spark.sql.catalog.demo.type=rest
spark.sql.catalog.demo.uri=http://iceberg-rest:8181
spark.sql.catalog.demo.warehouse=s3://warehouse/
spark.sql.catalog.demo.io-impl=org.apache.iceberg.aws.s3.S3FileIO
spark.sql.catalog.demo.s3.endpoint=http://minio:9000
spark.sql.catalog.demo.s3.path-style-access=true
```

## Smoke Query
```bash
docker exec -it spark-iceberg spark-sql \
  --conf spark.sql.catalog.demo=org.apache.iceberg.spark.SparkCatalog \
  --conf spark.sql.catalog.demo.type=rest \
  --conf spark.sql.catalog.demo.uri=http://iceberg-rest:8181 \
  --conf spark.sql.catalog.demo.warehouse=s3://warehouse/ \
  --conf spark.sql.catalog.demo.io-impl=org.apache.iceberg.aws.s3.S3FileIO \
  --conf spark.sql.catalog.demo.s3.endpoint=http://minio:9000 \
  --conf spark.sql.catalog.demo.s3.path-style-access=true \
  -e "SHOW NAMESPACES IN demo;"
```

## Dual-Path Note (MinIO)
- Default runnable path in this repo uses community-compatible MinIO container image.
- Official MinIO docs now emphasize AIStor packaging in some areas; if your org requires vendor-official enterprise path, map equivalent settings per AIStor docs and licensing terms.
