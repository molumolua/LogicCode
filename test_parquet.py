import pyarrow.parquet as pq
PATH = r"D:\Research\CodeAdapt\Code-Contests-Plus\default_single\part-00000-of-00010.parquet"

# 先只读 schema（不拉数据批），看能否通过
pf = pq.ParquetFile(PATH)
print("num_row_groups:", pf.num_row_groups)
print("schema:", pf.schema_arrow)

# 尝试读取一列（尽量挑“简单”标量列名，若不确定就先读第0列）
table = pq.read_table(PATH, memory_map=False)  # memory_map=False 更稳一些
print(table.shape)
