import { useRef,useEffect } from "react";
import * as THREE from 'three';
const AnimatedNetworkBackground = () => {
  const mountRef = useRef(null);
  const rendererRef = useRef(null);
  const animationIdRef = useRef(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    // Prevent double initialization (useful with StrictMode)
    if (rendererRef.current) return;

    // Scene + Camera + Renderer
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0f0f23);

    const camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    camera.position.z = 35;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.domElement.style.display = 'block';
    mount.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // --- Particle + line setup (kept similar to your logic) ---
    const particleCount = 120;
    const particles = [];
    const particleGeometry = new THREE.SphereGeometry(0.18, 8, 8);
    const particleMaterial = new THREE.MeshBasicMaterial({
      color: 0x4a9eff,
      transparent: true,
      opacity: 0.8
    });

    for (let i = 0; i < particleCount; i++) {
      const particle = new THREE.Mesh(particleGeometry, particleMaterial);
      particle.position.set(
        (Math.random() - 0.5) * 100,
        (Math.random() - 0.5) * 60,
        (Math.random() - 0.5) * 20
      );
      particle.userData = {
        velocity: new THREE.Vector3(
          (Math.random() - 0.5) * 0.035,
          (Math.random() - 0.5) * 0.035,
          (Math.random() - 0.5) * 0.018
        ),
        targetPosition: null,
        formationForce: new THREE.Vector3(),
        isInFormation: false
      };
      particles.push(particle);
      scene.add(particle);
    }

    // Lines
    const maxConnections = 200;
    const connectionDistance = 18;
    const lines = [];
    for (let i = 0; i < maxConnections; i++) {
      const lineGeometry = new THREE.BufferGeometry();
      const positions = new Float32Array(6);
      lineGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      const lineMaterial = new THREE.LineBasicMaterial({
        color: 0x4a9eff,
        transparent: true,
        opacity: 0.6,
        blending: THREE.AdditiveBlending
      });
      const line = new THREE.Line(lineGeometry, lineMaterial);
      line.visible = false;
      lines.push(line);
      scene.add(line);
    }

    // Formation helper (simplified copy of your function)
    const formationTypes = ['dna', 'tower', 'web', 'spiral', 'grid'];
    const generateFormation = (type, centerX, centerY, centerZ) => {
      const positions = [];
      const particlesPerFormation = Math.min(60, 120);
      switch (type) {
        case 'dna':
          for (let i = 0; i < particlesPerFormation; i++) {
            const t = (i / particlesPerFormation) * Math.PI * 8;
            const radius = 8;
            const height = (i / particlesPerFormation) * 40 - 20;
            const offset = (i % 2 === 0) ? 0 : Math.PI;
            positions.push(new THREE.Vector3(
              centerX + Math.cos(t + offset) * radius,
              centerY + height,
              centerZ + Math.sin(t + offset) * radius
            ));
          }
          break;
        case 'tower': {
          const floors = 8;
          const per = Math.floor(particlesPerFormation / floors);
          for (let floor = 0; floor < floors; floor++) {
            const y = centerY + (floor - floors / 2) * 6;
            const radius = 6 + Math.sin(floor * 0.5) * 3;
            for (let i = 0; i < per; i++) {
              const angle = (i / per) * Math.PI * 2;
              positions.push(new THREE.Vector3(
                centerX + Math.cos(angle) * radius,
                y,
                centerZ + Math.sin(angle) * radius
              ));
            }
          }
          break;
        }
        case 'web': {
          const rings = 6;
          for (let ring = 0; ring < rings; ring++) {
            const radius = (ring + 1) * 3;
            const inRing = Math.max(4, Math.floor(particlesPerFormation / rings));
            for (let i = 0; i < inRing; i++) {
              const angle = (i / inRing) * Math.PI * 2;
              positions.push(new THREE.Vector3(
                centerX + Math.cos(angle) * radius,
                centerY + (Math.random() - 0.5) * 4,
                centerZ + Math.sin(angle) * radius
              ));
            }
          }
          break;
        }
        case 'spiral':
          for (let i = 0; i < particlesPerFormation; i++) {
            const t = (i / particlesPerFormation) * Math.PI * 6;
            const radius = 4 + (i / particlesPerFormation) * 8;
            const height = (i / particlesPerFormation) * 30 - 15;
            positions.push(new THREE.Vector3(
              centerX + Math.cos(t) * radius,
              centerY + height,
              centerZ + Math.sin(t) * radius
            ));
          }
          break;
        case 'grid': {
          const gridSize = Math.ceil(Math.sqrt(particlesPerFormation));
          for (let i = 0; i < particlesPerFormation; i++) {
            const x = (i % gridSize) - gridSize / 2;
            const z = Math.floor(i / gridSize) - gridSize / 2;
            positions.push(new THREE.Vector3(
              centerX + x * 4,
              centerY + Math.sin(x * z * 0.3) * 3,
              centerZ + z * 4
            ));
          }
          break;
        }
      }
      return positions;
    };

    // Phase managers
    let formationPhase = 'wandering';
    let phaseTimer = Date.now();
    const phaseDurations = { wandering: 3000, forming: 2000, holding: 2500, breaking: 1500 };
    let currentFormation = null;

    // Animate loop
    const animate = () => {
      const now = Date.now();

      // Phase switching
      if (now - phaseTimer > phaseDurations[formationPhase]) {
        phaseTimer = now;
        if (formationPhase === 'wandering') {
          currentFormation = formationTypes[Math.floor(Math.random() * formationTypes.length)];
          const centerX = (Math.random() - 0.5) * 60;
          const centerY = (Math.random() - 0.5) * 30;
          const centerZ = (Math.random() - 0.5) * 10;
          const positions = generateFormation(currentFormation, centerX, centerY, centerZ);
          particles.forEach((p, i) => {
            if (i < positions.length) {
              p.userData.targetPosition = positions[i];
              p.userData.isInFormation = true;
            }
          });
          formationPhase = 'forming';
        } else if (formationPhase === 'forming') {
          formationPhase = 'holding';
        } else if (formationPhase === 'holding') {
          formationPhase = 'breaking';
        } else { // breaking
          particles.forEach(p => {
            p.userData.targetPosition = null;
            p.userData.isInFormation = false;
            p.userData.formationForce.set(0, 0, 0);
          });
          formationPhase = 'wandering';
        }
      }

      // Update particles
      particles.forEach(p => {
        const u = p.userData;
        if (formationPhase === 'forming' && u.targetPosition) {
          const dir = new THREE.Vector3().subVectors(u.targetPosition, p.position).normalize().multiplyScalar(0.02);
          u.formationForce.lerp(dir, 0.1);
          u.velocity.lerp(u.formationForce, 0.3);
        } else if (formationPhase === 'holding' && u.targetPosition) {
          const dir = new THREE.Vector3().subVectors(u.targetPosition, p.position).normalize().multiplyScalar(0.01);
          u.velocity.lerp(dir, 0.2);
        } else if (formationPhase === 'breaking') {
          u.velocity.multiplyScalar(1.1);
          u.velocity.add(new THREE.Vector3((Math.random() - 0.5) * 0.02, (Math.random() - 0.5) * 0.02, (Math.random() - 0.5) * 0.01));
        } else {
          u.velocity.x += (Math.random() - 0.5) * 0.0004;
          u.velocity.y += (Math.random() - 0.5) * 0.0004;
          u.velocity.z += (Math.random() - 0.5) * 0.0002;
        }

        p.position.add(u.velocity);

        // Wrap-around bounds
        if (p.position.x > 50) p.position.x = -50;
        if (p.position.x < -50) p.position.x = 50;
        if (p.position.y > 30) p.position.y = -30;
        if (p.position.y < -30) p.position.y = 30;
        if (p.position.z > 10) p.position.z = -10;
        if (p.position.z < -10) p.position.z = 10;

        u.velocity.clampLength(0, 0.05);
      });

      // Update connections
      let li = 0;
      lines.forEach(l => (l.visible = false));
      for (let i = 0; i < particles.length && li < lines.length; i++) {
        for (let j = i + 1; j < particles.length && li < lines.length; j++) {
          const dist = particles[i].position.distanceTo(particles[j].position);
          if (dist < connectionDistance) {
            const line = lines[li];
            const arr = line.geometry.attributes.position.array;
            arr[0] = particles[i].position.x;
            arr[1] = particles[i].position.y;
            arr[2] = particles[i].position.z;
            arr[3] = particles[j].position.x;
            arr[4] = particles[j].position.y;
            arr[5] = particles[j].position.z;
            line.geometry.attributes.position.needsUpdate = true;
            line.material.opacity = (1 - dist / connectionDistance) * 0.7;
            line.visible = true;
            li++;
          }
        }
      }

      // subtle camera movement
      const t = Date.now() * 0.0001;
      camera.position.x = Math.sin(t) * 2;
      camera.position.y = Math.cos(t * 0.7) * 1;
      camera.lookAt(0, 0, 0);

      renderer.render(scene, camera);
      animationIdRef.current = requestAnimationFrame(animate);
    };

    // Start
    animationIdRef.current = requestAnimationFrame(animate);

    // Resize handler
    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      if (animationIdRef.current) cancelAnimationFrame(animationIdRef.current);

      // remove canvas
      if (rendererRef.current && rendererRef.current.domElement && mount.contains(rendererRef.current.domElement)) {
        mount.removeChild(rendererRef.current.domElement);
      }
      // dispose renderer
      rendererRef.current?.dispose();
      rendererRef.current = null;

      // dispose geometries / materials
      particleGeometry.dispose();
      particleMaterial.dispose();
      lines.forEach(l => {
        l.geometry.dispose();
        if (l.material) l.material.dispose();
      });
    };
  }, []);

  return <div ref={mountRef} className="fixed inset-0 -z-10 pointer-events-none" />;
};

export default AnimatedNetworkBackground;
