import re
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
                "denoise": ("STRING", {"default": "1.0", "multiline": False}), 
                "vae_batch_size": ("INT", {"default": 4, "min": -1, "max": 64}),
                "configs_json": ("STRING", {"multiline": True, "default": '[{"sampler": "euler", "scheduler": "normal", "steps": 20, "cfg": 7.0}]'}),
                "resolutions_json": ("STRING", {"multiline": True, "default": '[[1024, 1024]]'}),
                "session_name": ("STRING", {"default": "my_session"}),
                "overwrite_existing": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "optional_model": ("MODEL",),
                "optional_clip": ("CLIP",),
                "optional_vae": ("VAE",),
                "optional_positive": ("CONDITIONING",),
                "optional_negative": ("CONDITIONING",),
                "optional_latent": ("LATENT",),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("dashboard_html",)
    FUNCTION = "run_tests"
    CATEGORY = "sampling/testing"

    # --- HELPER: PARSE LORA STACKS ---
    def parse_lora_definition(self, lora_string, global_model_strength, global_clip_strength):
        if lora_string == "None": return []
        definitions = []
        parts = lora_string.split(" + ")
        for part in parts:
            part = part.strip()
            if ":" in part:
                segments = part.split(":")
                name = segments[0].strip()
                m_str = float(segments[1]) if len(segments) > 1 else 1.0
                c_str = float(segments[2]) if len(segments) > 2 else 1.0
                definitions.append((name, m_str, c_str))
            else:
                definitions.append((part, global_model_strength, global_clip_strength))
        return definitions

    # --- HELPER: PARSE DYNAMIC FLOAT ARRAYS ---
    def parse_float_input(self, input_str):
        try:
            val = json.loads(input_str)
            if isinstance(val, list): return [float(x) for x in val]
            return [float(val)]
        except:
            try:
                if "," in input_str: return [float(x.strip()) for x in input_str.split(",")]
                return [float(input_str)]
            except:
                return [1.0]

    def run_tests(self, ckpt_name, positive_text, negative_text, seed, denoise, vae_batch_size, overwrite_existing, configs_json, resolutions_json, session_name, unique_id, optional_model=None, optional_clip=None, optional_vae=None, optional_positive=None, optional_negative=None, optional_latent=None):
        try:
            raw_configs = json.loads(configs_json.strip())
            resolutions = json.loads(resolutions_json.strip())
            denoise_values = self.parse_float_input(str(denoise))
        except Exception as e: raise ValueError(f"Parsing Error: {e}")

        # --- LOAD RESOURCES ---
        if optional_model is not None and optional_clip is not None and optional_vae is not None:
            model, clip, vae = optional_model, optional_clip, optional_vae
            model_name_for_meta = "External Model"
        else:
            ckpt_path = folder_paths.get_full_path("checkpoints", ckpt_name)
            out = comfy.sd.load_checkpoint_guess_config(ckpt_path, output_vae=True, output_clip=True, embedding_directory=folder_paths.get_folder_paths("embeddings"))
            model, clip, vae = out[:3]
            model_name_for_meta = ckpt_name

        if optional_positive is not None:
            positive = optional_positive
            pos_text_for_meta = "External Conditioning"
        else:
            tokens = clip.tokenize(positive_text)
            cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
            positive = [[cond, {"pooled_output": pooled}]]
            pos_text_for_meta = positive_text

        if optional_negative is not None:
            negative = optional_negative
            neg_text_for_meta = "External Conditioning"
        else:
            tokens = clip.tokenize(negative_text)
            cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
            negative = [[cond, {"pooled_output": pooled}]]
            neg_text_for_meta = negative_text

        session_name = re.sub(r'[^\w\-]', '', session_name)
        if not session_name: session_name = "default_session"

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
            
            for combo in itertools.product(samplers, schedulers, steps_l, cfgs, loras, str_m, str_c, denoise_values):
                expanded.append({
                    "sampler": combo[0], "scheduler": combo[1], "steps": combo[2],
                    "cfg": combo[3], "lora": combo[4], "str_model": combo[5], "str_clip": combo[6],
                    "denoise": combo[7]
                })

        print(f"[GridTester] Processing {len(expanded) * len(resolutions)} items...")

        cached_lora_key = None
        cached_model, cached_clip = None, None
        pending_batch = []
        
        # Keys that determine a "match"
        MATCH_KEYS = ["sampler", "scheduler", "steps", "cfg", "lora", "str_model", "str_clip", "denoise", "seed", "width", "height"]

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
                # --- CHECK FOR EXISTING MATCH ---
                match_index = -1
                for idx, item in enumerate(existing_data["items"]):
                    is_match = True
                    for k in MATCH_KEYS:
                        # Values in conf come from JSON inputs
                        val_conf = conf.get(k)
                        # Special handling for resolution/seed which aren't in 'conf' dict yet
                        if k == "width": val_conf = w
                        if k == "height": val_conf = h
                        if k == "seed": val_conf = seed
                        
                        # Compare
                        if item.get(k) != val_conf:
                            is_match = False
                            break
                    
                    if is_match:
                        match_index = idx
                        break

                if match_index != -1:
                    # Match Found!
                    if not overwrite_existing:
                        # Skip generation
                        print(f"[GridTester] Skipping existing config: {conf}")
                        continue
                    else:
                        # Overwrite mode: Delete old file and remove from manifest
                        print(f"[GridTester] Overwriting existing config...")
                        old_item = existing_data["items"][match_index]
                        # Extract filename from the URL-like string
                        # Format: /view?filename=img_123.webp&...
                        try:
                            old_fname_match = re.search(r'filename=([^&]+)', old_item["file"])
                            if old_fname_match:
                                old_fname = old_fname_match.group(1)
                                old_path = os.path.join(img_dir, old_fname)
                                if os.path.exists(old_path):
                                    os.remove(old_path)
                        except Exception as e:
                            print(f"Error cleaning up old file: {e}")
                        
                        # Remove from list (new one will be added at top later)
                        existing_data["items"].pop(match_index)

                # --- MODEL LOADING ---
                active_loras = self.parse_lora_definition(conf["lora"], conf["str_model"], conf["str_clip"])
                current_lora_key = tuple(active_loras)
                if current_lora_key == cached_lora_key and cached_model is not None:
                    curr_model, curr_clip = cached_model, cached_clip
                else:
                    curr_model, curr_clip = model, clip
                    for lora_def in active_loras:
                        lname, lstr_m, lstr_c = lora_def
                        path = folder_paths.get_full_path("loras", lname)
                        if path:
                            lora_data = comfy.utils.load_torch_file(path)
                            curr_model, curr_clip = comfy.sd.load_lora_for_models(curr_model, curr_clip, lora_data, lstr_m, lstr_c)
                    cached_lora_key = current_lora_key
                    cached_model, cached_clip = curr_model, curr_clip

                # --- LATENT SETUP ---
                if optional_latent is not None:
                    latent_in = {"samples": optional_latent["samples"].clone()}
                else:
                    latent_in = {"samples": torch.zeros([1, 4, h // 8, w // 8])}

                # Generate
                t0 = time.time()
                try:
                    result = nodes.common_ksampler(
                        model=curr_model, seed=seed, steps=conf["steps"], cfg=conf["cfg"],
                        sampler_name=conf["sampler"], scheduler=conf["scheduler"],
                        positive=positive, negative=negative, latent=latent_in, 
                        denoise=conf["denoise"]
                    )
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