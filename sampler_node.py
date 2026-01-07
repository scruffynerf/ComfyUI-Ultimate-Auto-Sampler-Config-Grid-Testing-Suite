import torch
import json
import os
import time
import random
import itertools
import folder_paths
import nodes
import comfy.utils
import comfy.sd
import comfy.samplers
from PIL import Image
import numpy as np
from .html_generator import get_html_template

class SamplerGridTester:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "ckpt_name": (folder_paths.get_filename_list("checkpoints"), ),
                "positive_text": ("STRING", {"multiline": True, "default": "masterpiece, best quality, 1girl"}),
                "negative_text": ("STRING", {"multiline": True, "default": "bad quality, worst quality, lowres"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                "denoise": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "vae_batch_size": ("INT", {"default": 4, "min": -1, "max": 64}),
                "configs_json": ("STRING", {"multiline": True, "default": '[{"sampler": "euler", "scheduler": "normal", "steps": 20, "cfg": 7.0}]'}),
                "resolutions_json": ("STRING", {"multiline": True, "default": '[[1024, 1024]]'}),
                "session_name": ("STRING", {"default": "my_session"}),
            },
            "optional": {
                "optional_model": ("MODEL",),
                "optional_clip": ("CLIP",),
                "optional_vae": ("VAE",),
                "optional_positive": ("CONDITIONING",),
                "optional_negative": ("CONDITIONING",),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("dashboard_html",)
    FUNCTION = "run_tests"
    CATEGORY = "sampling/testing"

    def run_tests(self, ckpt_name, positive_text, negative_text, seed, denoise, vae_batch_size, configs_json, resolutions_json, session_name, unique_id, optional_model=None, optional_clip=None, optional_vae=None, optional_positive=None, optional_negative=None):
        try:
            raw_configs = json.loads(configs_json.strip())
            resolutions = json.loads(resolutions_json.strip())
        except Exception as e: raise ValueError(f"JSON Parsing Error: {e}")

        # --- LOAD RESOURCES ---
        # 1. Model & Clip & VAE
        if optional_model is not None and optional_clip is not None and optional_vae is not None:
            model, clip, vae = optional_model, optional_clip, optional_vae
            model_name_for_meta = "External Model"
        else:
            ckpt_path = folder_paths.get_full_path("checkpoints", ckpt_name)
            out = comfy.sd.load_checkpoint_guess_config(ckpt_path, output_vae=True, output_clip=True, embedding_directory=folder_paths.get_folder_paths("embeddings"))
            model, clip, vae = out[:3]
            model_name_for_meta = ckpt_name

        # 2. Conditioning (Prompts) -- FIXED FORMATTING
        if optional_positive is not None:
            positive = optional_positive
            pos_text_for_meta = "External Conditioning"
        else:
            tokens = clip.tokenize(positive_text)
            cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
            # Wrap in the list structure ComfyUI samplers expect: [[cond, {"pooled_output": pooled}]]
            positive = [[cond, {"pooled_output": pooled}]]
            pos_text_for_meta = positive_text

        if optional_negative is not None:
            negative = optional_negative
            neg_text_for_meta = "External Conditioning"
        else:
            tokens = clip.tokenize(negative_text)
            cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
            # Wrap in the list structure ComfyUI samplers expect
            negative = [[cond, {"pooled_output": pooled}]]
            neg_text_for_meta = negative_text

        # --- SETUP FOLDERS & MANIFEST ---
        base_dir = os.path.join(folder_paths.get_output_directory(), "benchmarks", session_name)
        img_dir = os.path.join(base_dir, "images")
        os.makedirs(img_dir, exist_ok=True)
        manifest_path = os.path.join(base_dir, "manifest.json")

        existing_data = {"items": [], "meta": {}}
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r") as f:
                    d = json.load(f)
                    if isinstance(d, list): existing_data["items"] = d
                    else: existing_data = d
            except: pass

        # Update Session Meta
        existing_data["meta"] = {
            "model": model_name_for_meta,
            "positive": pos_text_for_meta,
            "negative": neg_text_for_meta,
            "updated": int(time.time())
        }

        # --- EXPAND CONFIGS ---
        ALL_SCHEDULERS = comfy.samplers.KSampler.SCHEDULERS
        ALL_SAMPLERS = comfy.samplers.KSampler.SAMPLERS
        expanded = []
        for entry in raw_configs:
            def to_list(x): return x if isinstance(x, list) else [x]
            samplers = ALL_SAMPLERS if entry.get("sampler") == "*" else to_list(entry.get("sampler", "euler"))
            schedulers = ALL_SCHEDULERS if entry.get("scheduler") == "*" else to_list(entry.get("scheduler", "normal"))
            steps_l = to_list(entry.get("steps", 20))
            cfgs = to_list(entry.get("cfg", 7.0))
            loras = to_list(entry.get("lora", "None"))
            str_m = to_list(entry.get("str_model", 1.0))
            str_c = to_list(entry.get("str_clip", 1.0))
            for combo in itertools.product(samplers, schedulers, steps_l, cfgs, loras, str_m, str_c):
                expanded.append({
                    "sampler": combo[0], "scheduler": combo[1], "steps": combo[2],
                    "cfg": combo[3], "lora": combo[4], "str_model": combo[5], "str_clip": combo[6]
                })

        print(f"[GridTester] Processing {len(expanded) * len(resolutions)} items...")

        # --- CACHING & BATCHING ---
        cached_lora_key = None
        cached_model, cached_clip = None, None
        pending_batch = []
        
        def flush_batch(batch_list):
            if not batch_list: return
            latents_to_decode = torch.cat([x[0] for x in batch_list], dim=0)
            decoded = vae.decode(latents_to_decode)
            
            for i, img_tensor in enumerate(decoded):
                img_np = 255. * img_tensor.cpu().numpy()
                img = Image.fromarray(np.clip(img_np, 0, 255).astype(np.uint8))
                meta = batch_list[i][1]
                ts = int(time.time() * 100000) + random.randint(0,1000)
                filename = f"img_{ts}.webp"
                img.save(os.path.join(img_dir, filename), quality=80)
                meta.update({
                    "id": ts, 
                    "file": f"/view?filename={filename}&type=output&subfolder=benchmarks/{session_name}/images",
                    "rejected": False
                })
                existing_data["items"].insert(0, meta)
        
        for res in resolutions:
            w, h = res[0], res[1]
            flush_batch(pending_batch)
            pending_batch = []

            for conf in expanded:
                # --- MODEL LOADING LOGIC ---
                current_lora_key = (conf["lora"], conf["str_model"], conf["str_clip"])
                
                # Check cache
                if current_lora_key == cached_lora_key and cached_model is not None:
                    curr_model, curr_clip = cached_model, cached_clip
                else:
                    # Reset to base
                    curr_model, curr_clip = model, clip
                    # Apply LoRA if needed
                    if conf["lora"] != "None":
                        path = folder_paths.get_full_path("loras", conf["lora"])
                        if path:
                            lora_data = comfy.utils.load_torch_file(path)
                            curr_model, curr_clip = comfy.sd.load_lora_for_models(curr_model, curr_clip, lora_data, conf["str_model"], conf["str_clip"])
                    
                    cached_lora_key = current_lora_key
                    cached_model, cached_clip = curr_model, curr_clip

                # Generate
                latent_in = {"samples": torch.zeros([1, 4, h // 8, w // 8])}
                t0 = time.time()
                try:
                    result = nodes.common_ksampler(model=curr_model, seed=seed, steps=conf["steps"], cfg=conf["cfg"],
                                                   sampler_name=conf["sampler"], scheduler=conf["scheduler"],
                                                   positive=positive, negative=negative, latent=latent_in, denoise=denoise)
                except Exception as e:
                    print(f"Generation Failed: {e}")
                    continue
                
                duration = round(time.time() - t0, 3)
                meta = conf.copy()
                meta.update({"width": w, "height": h, "duration": duration, "seed": seed})
                pending_batch.append((result[0]["samples"], meta))
                
                if vae_batch_size != -1 and len(pending_batch) >= vae_batch_size:
                    flush_batch(pending_batch)
                    pending_batch = []

        flush_batch(pending_batch)

        with open(manifest_path, "w") as f: json.dump(existing_data, f, indent=4)
        
        html = get_html_template(session_name, existing_data, unique_id)
        return (html,)