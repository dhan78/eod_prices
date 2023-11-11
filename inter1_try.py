import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

def plot_row(array1, array2, array3, row_number):
    if row_number < 0 or row_number >= array1.shape[0]:
        print("Row number is out of range.")
        return

    plt.scatter(range(array1.shape[1]), array1[row_number], c='red', marker='o', label='array1', s=50)
    plt.scatter(range(array2.shape[1]), array2[row_number], c='red', marker='o', label='array2', s=50)
    plt.plot(array3[row_number], label='array3')

    plt.xlabel('Column')
    plt.ylabel('Value')
    plt.title(f'Row Comparison for Row {row_number}')
    plt.legend()
    plt.show()

def interpolate_rows(array1, array2, array3):
    interpolated_array = np.zeros((array1.shape[0], array3.shape[1]))

    for i in range(array1.shape[0]):
        x = array1[i]
        y = array2[i]

        # Use linear interpolation to estimate Y for elements in array3
        f = interp1d(x, y, kind='quadratic', fill_value='extrapolate')
        interpolated_array[i] = f(array3[i])

    return interpolated_array

# Create the 25000x4 NumPy array (array1)
num_rows = 25000
num_columns = 4
array1 = np.random.rand(num_rows, num_columns)  # Generate random values between 0 and 1

# Shuffle the rows to create array2
array2 = array1[np.random.permutation(num_rows)]

# Create array3 with 100 columns and shuffled values from array1
array3 = np.random.rand(num_rows, 100)

# Interpolate Y for elements in array3 using array1 and array2
interpolated_array3 = interpolate_rows(array1, array2, array3)

# Specify the row number you want to plot
row_to_plot = 10

# Call the plot_row function to plot the specified row
# plot_row(array1, array2, array3, row_to_plot)
