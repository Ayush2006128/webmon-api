const container = document.getElementById('canvas-container');

if (container) {
    // Clear the static CSS background since we are using Three.js
    container.style.background = 'none';

    // Scene, Camera, Renderer
    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // GLSL Shader Material for fluid neon effect
    const vertexShader = `
        varying vec2 vUv;
        void main() {
            vUv = uv;
            gl_Position = vec4(position, 1.0);
        }
    `;

    const fragmentShader = `
        uniform float time;
        uniform vec2 resolution;
        varying vec2 vUv;

        // Simple 2D noise function for more organic fluid feel
        float random(vec2 st) {
            return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123);
        }

        void main() {
            vec2 uv = vUv;
            vec2 p = uv * 2.0 - 1.0;
            p.x *= resolution.x / resolution.y;
            
            float t = time * 0.25; // slightly faster for more dynamic fluid
            
            // Fluid distortion waves - scale them up to make them look closer
            float wave1 = sin(p.x * 1.2 + t) * cos(p.y * 1.2 + t * 1.2);
            float wave2 = sin(p.x * 1.8 - t * 0.8) * cos(p.y * 1.5 + t * 0.5);
            float wave3 = sin(p.x * 2.5 + t * 1.5) * cos(p.y * 2.5 - t * 1.0);
            
            float noise = wave1 + wave2 + (wave3 * 0.5);
            
            // Base dark color matches #050505
            vec3 color = vec3(0.02, 0.02, 0.02);
            
            // Normalize noise to roughly 0-1
            float n = noise * 0.4 + 0.5;
            
            // Sharper, brighter glowing blobs instead of blurry gradients
            // Using smoothstep with a tighter range for distinct shapes
            float cyanGlow = smoothstep(0.5, 0.7, n) * 0.6;
            float pinkGlow = smoothstep(0.5, 0.7, 1.0 - n) * 0.6;
            
            // Add sharp highlights to make it look like a glossy fluid
            float cyanHighlight = smoothstep(0.65, 0.7, n) * 0.8;
            float pinkHighlight = smoothstep(0.65, 0.7, 1.0 - n) * 0.8;
            
            vec3 cyan = vec3(0.0, 0.9, 1.0); // #00E5FF
            vec3 pink = vec3(1.0, 0.0, 0.5); // #FF007F
            
            color += cyan * (cyanGlow + cyanHighlight);
            color += pink * (pinkGlow + pinkHighlight);
            
            // Subtle vignette to focus the center
            float dist = length(uv - 0.5);
            color *= smoothstep(1.1, 0.2, dist);

            gl_FragColor = vec4(color, 1.0);
        }
    `;

    const uniforms = {
        time: { value: 0.0 },
        resolution: { value: new THREE.Vector2(window.innerWidth, window.innerHeight) }
    };

    const material = new THREE.ShaderMaterial({
        vertexShader,
        fragmentShader,
        uniforms,
        transparent: true
    });

    const geometry = new THREE.PlaneGeometry(2, 2);
    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);

    // Animation Loop
    let clock = new THREE.Clock();
    function animate() {
        requestAnimationFrame(animate);
        uniforms.time.value = clock.getElapsedTime();
        renderer.render(scene, camera);
    }
    animate();

    // Resize Handler
    window.addEventListener('resize', () => {
        renderer.setSize(window.innerWidth, window.innerHeight);
        uniforms.resolution.value.set(window.innerWidth, window.innerHeight);
    });
}
