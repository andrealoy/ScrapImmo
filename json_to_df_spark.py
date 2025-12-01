from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, lit

spark = SparkSession.builder \
    .appName("JSON Processing") \
    .getOrCreate()
df = spark.read.option("multiLine" , True).json("/home/andreal/Documents/dev/projet_scrap/jsons/details/")
df.printSchema() 



# fields = [
#     "brand",
#     "id",
#     "metadata.creationDate",
#     "metadata.updateDate",
#     "sections.location.address.city",
#     "sections.location.address.zipCode",
#     "sections.location.address.country",
#     "sections.location.geometry.type",
#     "sections.location.geometry.coordinates",
#     "sections.description.description",
#     "sections.description.headline",
#     "sections.hardFacts.title",
#     "sections.hardFacts.keyfacts",
#     "sections.hardFacts.facts",
#     "sections.hardFacts.price.value"
# ]

# df_selected = df.select([col(f).alias(f.replace(".", "_")) for f in fields])
# df_exploded = df_selected.withColumn("fact", explode("sections_hardFacts_facts"))

# df_facts = df_exploded \
#     .select(
#         "*",
#         col("fact.type").alias("fact_type"),
#         col("fact.value").alias("fact_value")
#     ) \
#     .groupBy([c for c in df_selected.columns if c != "sections_hardFacts_facts"]) \
#     .pivot("fact_type") \
#     .agg({"fact_value": "first"})
# final_df = df_facts.drop("sections_hardFacts_facts")
# final_df.repartition(1).write.csv(
#     "scraped_results_spark",
#     header=True,
#     encoding="utf-8"
# )
