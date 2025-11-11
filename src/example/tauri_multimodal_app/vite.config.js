import { defineConfig } from 'vite';

export default defineConfig({
  root: 'dist',  // <-- look for index.html here
  build: {
    outDir: '../dist-build', // output folder for Vite build, can be src-tauri/../dist-build
    emptyOutDir: true
  }
});
