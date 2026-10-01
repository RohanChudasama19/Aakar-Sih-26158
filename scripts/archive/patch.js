  // HEATMAP INTEGRATION
  function applyHeatmapColors(colorsBuffer) {
    if (!currentRepObject) return;
    currentRepObject.traverse(o => {
      if (o.isMesh && o.geometry) {
        if (!o.geometry.isNonIndexed && o.geometry.index) {
          o.geometry = o.geometry.toNonIndexed();
        }
        
        if (colorsBuffer && o.geometry.attributes.position.count * 3 === colorsBuffer.length) {
            o.geometry.setAttribute('heatmapColor', new THREE.BufferAttribute(colorsBuffer, 3));
        } else if (colorsBuffer) {
            console.warn(`Face mapping mismatch! Vertices: ${o.geometry.attributes.position.count}, Colors: ${colorsBuffer.length/3}`);
            const errColors = new Float32Array(o.geometry.attributes.position.count * 3);
            for(let i=0; i<errColors.length; i+=3) { errColors[i] = 1; errColors[i+2] = 1; }
            o.geometry.setAttribute('heatmapColor', new THREE.BufferAttribute(errColors, 3));
        }
        
        if (!o.material.isHeatmapPatched) {
          const originalOnBeforeCompile = o.material.onBeforeCompile;
          o.material.userData.heatmapOpacity = { value: 0.0 };
          o.material.onBeforeCompile = (shader) => {
            shader.uniforms.heatmapOpacity = o.material.userData.heatmapOpacity;
            
            shader.vertexShader = `
              attribute vec3 heatmapColor;
              varying vec3 vHeatmapColor;
            ` + shader.vertexShader.replace(
              'void main() {',
              'void main() {\n  vHeatmapColor = heatmapColor;'
            );
            
            shader.fragmentShader = `
              uniform float heatmapOpacity;
              varying vec3 vHeatmapColor;
            ` + shader.fragmentShader.replace(
              '#include <dithering_fragment>',
              `#include <dithering_fragment>
               gl_FragColor = mix(gl_FragColor, vec4(vHeatmapColor, gl_FragColor.a), heatmapOpacity);
              `
            );
            
            if (originalOnBeforeCompile) originalOnBeforeCompile(shader);
          };
          o.material.isHeatmapPatched = true;
          o.material.needsUpdate = true;
        }
      }
    });
  }

  function setHeatmapOpacity(opacity) {
    if (!currentRepObject) return;
    currentRepObject.traverse(o => {
      if (o.isMesh && o.material && o.material.userData.heatmapOpacity) {
        o.material.userData.heatmapOpacity.value = opacity;
      }
    });
  }
