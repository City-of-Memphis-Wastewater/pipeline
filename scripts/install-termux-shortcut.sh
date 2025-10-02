mkdir -p $HOME/.shortcuts
mv run_eds_plot.sh $HOME/.shortcuts/
3.  **Make Executable:** You must ensure the script has execution permission:
```bash
chmod +x $HOME/.shortcuts/run_eds_plot.sh
4.  **Configure:** Don't forget to **update the `PROJECT_DIR`** variable inside the script to point to the actual location of your Python project!