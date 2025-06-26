import pygal
from pathlib import Path

#def plotsvg(x_data, y_data_dict,title=None,filename=None):
def plotsvg(data_dictdict,title=None,filename=None):
    # a dictlist might be better, each with its own x and y values, 
    
    if not title:
        title = 'Scatter Plot Example'
    if not filename:
        filename = 'media/scatter.svg'
    elif filename.endswith('.png'):
        filename = filename.replace('.png','.svg')
    Path(filename).parent.mkdir(parents=True, exist_ok=True)

    x_data = data_dictdict['x']
    scatter_chart = pygal.XY(stroke=True)
    scatter_chart.title = title
    for key, y_vec in y_data_dict.items():
        points = list(zip(x_data, y_vec))
        scatter_chart.add(key, points)
    scatter_chart.render_to_file(filename)
    #svg2png(filename)
    return scatter_chart

# Cairo requires GTK binaries, not currently included in this implementation.
def svg2png(filename):
    import cairosvg
    cairosvg.svg2png(url=filename, write_to=filename.replace('svg','png'))
