'use client';

import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

export type AgentUIState = 'ready' | 'connecting' | 'thinking' | 'listening' | 'speaking' | 'ended';

interface ParticleSwarmCanvasProps {
  agentState: AgentUIState;
  className?: string;
}

export function ParticleSwarmCanvas({ agentState, className }: ParticleSwarmCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const stateRef = useRef<AgentUIState>(agentState);

  useEffect(() => {
    stateRef.current = agentState;
  }, [agentState]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Wide, zoomed-out field — never fills the face of the camera
    const COUNT = 7000;
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x020617, 0.0045);

    const camera = new THREE.PerspectiveCamera(
      42,
      Math.max(container.clientWidth, 1) / Math.max(container.clientHeight, 1),
      0.1,
      5000
    );
    // Pull back further so the tunnel reads as atmosphere, not a tunnel wall
    camera.position.set(0, 0, 280);

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      powerPreference: 'high-performance',
      alpha: true,
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);

    const dummy = new THREE.Object3D();
    const color = new THREE.Color();
    const target = new THREE.Vector3();

    const geometry = new THREE.TetrahedronGeometry(0.22);
    const material = new THREE.MeshBasicMaterial({ color: 0xffffff });

    const instancedMesh = new THREE.InstancedMesh(geometry, material, COUNT);
    instancedMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    scene.add(instancedMesh);

    const positions: THREE.Vector3[] = [];
    for (let i = 0; i < COUNT; i++) {
      positions.push(
        new THREE.Vector3(
          (Math.random() - 0.5) * 130,
          (Math.random() - 0.5) * 130,
          (Math.random() - 0.5) * 130
        )
      );
      instancedMesh.setColorAt(i, color.setHex(0x10b981));
    }

    const clock = new THREE.Clock();
    let animationFrameId = 0;
    let rotationY = 0;
    const goldenRatio = (1.0 + Math.sqrt(5.0)) / 2.0;

    function animate() {
      animationFrameId = requestAnimationFrame(animate);

      const time = clock.getElapsedTime();
      const currentAppState = stateRef.current;

      let speed = 0.14;
      let chaos = 8.0;
      let coreSize = 10.0;
      let hueOffset = 0.48;
      let rotateSpeed = 0.15;

      if (currentAppState === 'ready') {
        speed = 0.14;
        chaos = 8.0;
        coreSize = 10.0;
        hueOffset = 0.48;
        rotateSpeed = 0.12;
      } else if (currentAppState === 'connecting') {
        speed = 0.55;
        chaos = 28.0;
        coreSize = 5.0;
        hueOffset = 0.72;
        rotateSpeed = 0.35;
      } else if (currentAppState === 'thinking') {
        speed = 0.4;
        chaos = 20.0;
        coreSize = 7.0;
        hueOffset = 0.58;
        rotateSpeed = 0.28;
      } else if (currentAppState === 'listening') {
        speed = 0.32;
        chaos = 16.0;
        coreSize = 8.0;
        hueOffset = 0.52;
        rotateSpeed = 0.2;
      } else if (currentAppState === 'speaking') {
        speed = 0.7;
        chaos = 14.0;
        coreSize = 16.0;
        hueOffset = 0.12;
        rotateSpeed = 0.4;
      } else if (currentAppState === 'ended') {
        speed = 0.06;
        chaos = 4.0;
        coreSize = 14.0;
        hueOffset = 0.6;
        rotateSpeed = 0.08;
      }

      rotationY += rotateSpeed * 0.01;
      instancedMesh.rotation.y = rotationY;

      for (let i = 0; i < COUNT; i++) {
        const norm = i / COUNT;
        const progress = (norm + time * speed * 0.2) % 1.0;
        const easeProgress = Math.pow(progress, 1.5);

        const theta = (2.0 * Math.PI * i) / goldenRatio;
        const phi = Math.acos(1.0 - 2.0 * norm);
        const currentRadius = coreSize + 160.0 * (1.0 - easeProgress);

        const instability = Math.pow(1.0 - progress, 2.0);
        const wobbleX = Math.sin(time * 2.0 + norm * 100.0) * chaos * instability;
        const wobbleY = Math.cos(time * 1.5 + norm * 200.0) * chaos * instability;
        const wobbleZ = Math.sin(time * 3.0 - norm * 300.0) * chaos * instability;

        const sinPhi = Math.sin(phi);
        const x = currentRadius * sinPhi * Math.cos(theta) + wobbleX;
        const y = currentRadius * sinPhi * Math.sin(theta) + wobbleY;
        const z = currentRadius * Math.cos(phi) + wobbleZ;

        target.set(x, y, z);

        const hue = (hueOffset + 0.25 * progress) % 1.0;
        const saturation = 0.85 + 0.15 * progress;
        const corePulse = progress > 0.92 ? Math.sin(time * 8.0) * 0.35 : 0.0;
        const lightness = Math.max(0.1, Math.min(0.9, 0.25 + 0.55 * progress + corePulse));

        color.setHSL(hue, saturation, lightness);

        positions[i].lerp(target, 0.08);
        dummy.position.copy(positions[i]);
        dummy.updateMatrix();
        instancedMesh.setMatrixAt(i, dummy.matrix);
        instancedMesh.setColorAt(i, color);
      }

      instancedMesh.instanceMatrix.needsUpdate = true;
      if (instancedMesh.instanceColor) {
        instancedMesh.instanceColor.needsUpdate = true;
      }

      renderer.render(scene, camera);
    }

    animate();

    const handleResize = () => {
      if (!container) return;
      const width = container.clientWidth;
      const height = container.clientHeight;
      if (width === 0 || height === 0) return;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      geometry.dispose();
      material.dispose();
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className={`pointer-events-none absolute inset-0 z-0 overflow-hidden ${className || ''}`}
    />
  );
}
