from nicegui import ui
import logging
import plotly.graph_objs as go


# Setup logger
logger = logging.getLogger('nicegui')
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def on_console_level_change(level):
    lvl = getattr(logging, level)
    console_handler.setLevel(lvl)
    logger.info(f'Console log level set to {level}')


def on_file_level_change(level):
    # Placeholder: Implement file handler logic here
    logger.info(f'File log level set to {level} (not implemented)')


def create_plot():
    if False:
        x_data = [0, 1, 2, 3, 4, 5]
        y_data = [0, 1, 4, 9, 16, 25]

        fig = go.Figure(
            data=[go.Scatter(x=x_data, y=y_data, mode='lines+markers', name='y = x^2')],
            layout=go.Layout(title='Simple 2D Plot', xaxis_title='X Axis', yaxis_title='Y Axis')
        )
        return fig
    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[0,1,2,3,4,5], y=[0,1,4,9,16,25], mode='lines', name='y=x^2'))
        fig.update_layout(title='Simple 2D Plot', 
                          xaxis_title='X Axis', 
                          yaxis_title='Y Axis',
                          autosize=True,
                          margin=dict(l=60, r=20, t=40, b=60))
        return fig


def main():
    with ui.row().style('height: 100vh;'):
        with ui.column().style('flex: 1; padding: 10px; max-width: 400px;'):
            ui.label('Adjust Log Levels')
            ui.select(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], label='Console Log Level', value='INFO').on('update', lambda e: on_console_level_change(e.value)).style('min-width: 200px;')
            ui.select(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], label='File Log Level', value='INFO').on('update', lambda e: on_file_level_change(e.value)).style('min-width: 200px;')
            ui.separator()
            ui.label('Logs:')
            log_area = ui.textarea().style('height: 300px;')#.bind_value('')  # bind later if needed

        with ui.column().style('flex: 3; padding: 10px;min-width: 400px;'):
            #ui.plotly(create_plot()).style('height: 400px; width: 100%')
            #ui.plotly(create_plot()).style('height: 100%; width: 100%;')
            ui.plotly(create_plot()).style('height: 400px; width: 100%; min-width: 400px;')


    ui.run()



main()
