import matplotlib.pyplot as plt
import numpy as np

# Sample data
x = np.linspace(0, 10, 100)
y1 = np.sin(x)
y2 = np.exp(x / 5)

# Create the first plot
fig, ax1 = plt.subplots()
ax1.plot(x, y1, 'b-', label='Sine Wave')
ax1.set_xlabel('X-axis')
ax1.set_ylabel('Sine', color='b')
ax1.tick_params(axis='y', labelcolor='b')

# Create the second y-axis
ax2 = ax1.twinx()
ax2.plot(x, y2, 'r--', label='Exponential')
ax2.set_ylabel('Exponential', color='r')
ax2.tick_params(axis='y', labelcolor='r')

# Add a title and show the plot
plt.title('Second Y-Axis Example')
plt.show()