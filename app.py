with perfume_col:
    # --- PHOTOREALISTIC BASE64 LOCAL VAULT FRAME WITH ANTI-SPAM AUDIO ENGINE ---
    if jpg_base64 and bdc_base64:
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
            body {{
                background-color: transparent;
                margin: 0;
                padding: 0;
                overflow: hidden;
                font-family: sans-serif;
            }}
            .container-vault {{
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                position: relative;
                padding-right: 20px;
            }}
            .label-status {{
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 5px;
                letter-spacing: 0.5px;
                text-shadow: 0px 2px 5px rgba(0,0,0,0.9);
                opacity: 0.9;
            }}
            .shelf-row {{
                display: flex;
                flex-direction: row;
                align-items: flex-end;
                justify-content: center;
                gap: 25px;
                position: relative;
                margin-top: 20px;
            }}
            .perfume-item {{
                position: relative;
                cursor: pointer;
            }}
            .real-bottle {{
                object-fit: contain;
                background: transparent !important;
                filter: drop-shadow(0px 12px 24px rgba(0,0,0,0.85));
                transition: transform 0.08s ease-in-out;
                -webkit-user-drag: none;
                user-select: none;
            }}
            .img-jpg {{ height: 230px; }}
            .img-bdc {{ height: 205px; }}

            .perfume-item:active .real-bottle {{
                transform: scale(0.94) translateY(4px);
            }}
            
            .mist-particle {{
                position: absolute;
                border-radius: 50%;
                pointer-events: none;
                filter: blur(3px);
                animation: blowOut 0.45s cubic-bezier(0.1, 0.8, 0.25, 1) forwards;
            }}
            @keyframes blowOut {{
                0% {{
                    width: 2px;
                    height: 2px;
                    left: var(--start-x);
                    top: var(--start-y);
                    opacity: 1;
                }}
                100% {{
                    width: 130px;
                    height: 95px;
                    left: calc(var(--start-x) + var(--move-x) - 65px);
                    top: calc(var(--start-y) + var(--move-y) - 45px);
                    opacity: 0;
                }}
            }}
            </style>
        </head>
        <body>
            <div class="container-vault">
                <div id="status-text" class="label-status">Active Spray: Le Male Elixir</div>
                
                <div class="shelf-row">
                    <div class="perfume-item" onclick="triggerSpray(event, 'jpg')">
                        <img class="real-bottle img-jpg" src="{jpg_base64}" alt="Le Male Elixir">
                    </div>

                    <div class="perfume-item" onclick="triggerSpray(event, 'bdc')">
                        <img class="real-bottle img-bdc" src="{bdc_base64}" alt="Bleu De Chanel">
                    </div>
                </div>
            </div>

            <script>
            // Global Persistent Audio Engine Settings to prevent crashing on multi-clicks
            let audioCtx = null;
            let noiseBuffer = null;

            function initAudioEngine() {{
                try {{
                    const AudioContext = window.AudioContext || window.webkitAudioContext;
                    if (!AudioContext) return;
                    audioCtx = new AudioContext();
                    
                    // Pre-generate White Noise Waveform Buffer once in memory
                    const bufSize = audioCtx.sampleRate * 0.45; 
                    noiseBuffer = audioCtx.createBuffer(1, bufSize, audioCtx.sampleRate);
                    const data = noiseBuffer.getChannelData(0);
                    for (let i = 0; i < bufSize; i++) {{
                        data[i] = Math.random() * 2 - 1;
                    }}
                }} catch (e) {{
                    console.log("AudioContext initialization delayed until click event", e);
                }}
            }}

            function playSpritzSound() {{
                // Initialize context on the first interactive click if not yet active
                if (!audioCtx) initAudioEngine();
                if (!audioCtx || !noiseBuffer) return;

                // Resume automatically if browser put the context to sleep
                if (audioCtx.state === 'suspended') {{
                    audioCtx.resume();
                }}

                try {{
                    const noiseSource = audioCtx.createBufferSource();
                    noiseSource.buffer = noiseBuffer;
                    
                    // Highpass Filter to lock in crisp premium air mist pressure
                    const filter = audioCtx.createBiquadFilter();
                    filter.type = 'highpass';
                    filter.frequency.value = 6500; 
                    
                    // Audio Envelope Curve (Instant punch drop down to soft release)
                    const gain = audioCtx.createGain();
                    gain.gain.setValueAtTime(0, audioCtx.currentTime);
                    gain.gain.linearRampToValueAtTime(0.25, audioCtx.currentTime + 0.01);
                    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.4);
                    
                    // Audio Pipeline Node Mapping
                    noiseSource.connect(filter);
                    filter.connect(gain);
                    gain.connect(audioCtx.destination);
                    
                    noiseSource.start();
                }} catch (err) {{
                    console.log("Audio block engine bypass error during spam click", err);
                }}
            }}

            function triggerSpray(event, type) {{
                const container = event.currentTarget;
                const statusLabel = document.getElementById('status-text');
                
                if (type === 'jpg') {{
                    statusLabel.innerText = "Active Spray: Le Male Elixir";
                }} else {{
                    statusLabel.innerText = "Active Spray: Bleu de Chanel";
                }}
                
                // Fire persistent audio engine trigger
                playSpritzSound();
                
                // Spray release point tracking
                const startX = "50%";
                const startY = type === 'jpg' ? "10px" : "15px";
                
                const colorGrad = type === 'jpg' 
                    ? 'radial-gradient(circle, rgba(212,175,55,0.65) 0%, rgba(139,107,14,0) 75%)'
                    : 'radial-gradient(circle, rgba(235,245,255,0.55) 0%, rgba(160,190,240,0) 75%)';

                for (let i = 0; i < 10; i++) {{
                    const p = document.createElement('div');
                    p.classList.add('mist-particle');
                    p.style.background = colorGrad;
                    p.style.setProperty('--start-x', startX);
                    p.style.setProperty('--start-y', startY);
                    
                    const angle = (Math.random() * 40 - 75) * (Math.PI / 180); 
                    const dist = Math.random() * 90 + 75;
                    
                    p.style.setProperty('--move-x', Math.cos(angle) * dist + 'px');
                    p.style.setProperty('--move-y', Math.sin(angle) * dist + 'px');
                    p.style.animationDuration = (Math.random() * 0.12 + 0.38) + 's';
                    
                    container.appendChild(p);
                    setTimeout(() => {{ p.remove(); }}, 450);
                }}
            }}
            </script>
        </body>
        </html>
        """
        components.html(html_code, height=360, scrolling=False)
    else:
        st.warning("⚠️ Pakisiguradong nailagay mo na ang 'jpg_elixir.png' at 'bdc.png' sa iyong project folder para lumitaw ang mga bote nang walang white background.")
