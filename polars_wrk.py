
# Groupby collect as list
import polars as pl

# Create a DataFrame
df = pl.DataFrame({
    'group': ['A', 'A', 'B', 'B', 'A', 'B'],
    'value': [1, 2, 3, 4, 5, 6]
})

# Group by 'group' column and collect 'value' column as a list in a new column 'value_list'
grouped_df = df.groupby('group').agg(pl.col('value').alias('value_list'))

# Display the grouped DataFrame
print(grouped_df)


# Filter groupbed df by list:
import polars as pl

# Create a list of values with duplicate entries
my_list = [[1, 2, 3], [4, 5], [6, 7, 8, 9], [1, 2, 3], [4, 5], [6, 7, 8, 9],[99,0]]

# Create a Polars series from the list
list_column = pl.Series("list_column", my_list)

# Create the dataframe
loss_df = pl.DataFrame({
    'column1': [1, 2, 3, 4, 5, 6,9],
    'list_column': list_column
})

# Define the values to filter
filter_values = [5]

# Filter the dataframe using a lambda function
filtered_df = loss_df.filter(pl.col("list_column").apply(lambda list_val: any(elem in filter_values for elem in list_val)))

# Display the filtered dataframe
print(filtered_df)


# import polars as pl
#
# # Create a DataFrame with a column of lists
# loss_df = pl.DataFrame({
#     "column_name": [[1, 2, 3], [4, 5], [6, 7, 8, 9]],
#     "new_column3": [True, False, True],
#     "new_column4": [0.5, 1.2, 2.3],
#     "new_column5": ["X", "Y", "Z"],
#     "new_column6": [False, True, False]
# })
#
# # Explode the column of lists into rows
# exploded_data = loss_df.explode("column_name")
#
# # Print the resulting DataFrame
# print(exploded_data)


