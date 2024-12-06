# 13. REPL

The REPL (Read-Eval-Print Loop) is a simple, interactive computer programming environment that takes single user inputs (i.e., single expressions), evaluates them, and returns the result to the user. The REPL allows you to simply plot data and visualize it in real-time. We recommend using the REPL for quick data visualization and exploration.

## Pros of plotting in REPL

- Real-time visualization
- Easy to explore data from python REPL
- Quick to generate plots
- Analyze data deeply by using backends of `matplotlib`

## Example of Python REPL in neovim

```{raw} html
<style>
  .video-container {
    display: flex;
    justify-content: center; 
    align-items: center; 
    max-height: 100vh;
  }

  .responsive-video {
    max-width: 80%; 
    height: auto; 
  }
</style>

<div class="video-container">
  <video class="responsive-video" autoplay muted loop controls>
    <source src="../../_static/repl_tutorial.mp4" type="video/mp4">
    Your browser does not support the video tag.
  </video>
</div>
```

## Reccomended Configuration of gsplot for REPL

```json
{
  "rich": {
    "traceback": {}
  },
  "rcParams": {
    "backends": "!Your_Backend!"
  },
  "axes": {
    "ion": true,
    "clear": true
  },
  "show": {
    "show": true
  },
}
```

If you want to specify the backends of `matplotlib`, you can add `rcParams: {"backends": "your_backend"}` to the configuration. For Mac users, you can use `rcParams: {"backends": "MacOSX"}`.
