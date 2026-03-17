#!/usr/bin/env python3

import os
import platform
from tkinter import filedialog
import sys
import zipfile
import shutil
import json
import urllib.request
import copy

'''
The script can be run as a dispatcher(Menu-driven interface) or
as a command line tool. For the command line tool, the usage is:
python main.py <filename> <init_stage> <final_stage>

Where:
- <init_stage> is the initial version of the datapack (1-6).
- <final_stage> is the final version to upgrade to (2-7).
1: 1.21/1.21.1
2: 1.21.2/1.21.3
3: 1.21.4/1.21.5/1.21.6
4: 1.21.7/1.21.8
5: 1.21.9/1.21.10
6: 1.21.11
7: 26.1
'''

configured_feature_refs = {}
configured_feature_objs = {}

def cls():
    command = 'cls' if platform.system().lower() == 'windows' else 'clear'
    os.system(command)

def read_classpath(zipfilename):
    print(f"Reading classpath {zipfilename}")
    with zipfile.ZipFile(zipfilename, mode="r") as zfo:
        for entry in zfo.namelist():
            split = entry.split("/")
            while len(split) > 0 and split[0] != "data":
                split = split[1:]
            if len(split) == 5 and split[0] == "data" and split[2] == "worldgen" and split[3] == "placed_feature" and split[4].endswith(".json"):
                print(f"\tScanning {entry}")
                with zfo.open(entry) as f:
                    obj = json.load(f)
                if not obj["feature"] in configured_feature_refs:
                    configured_feature_refs[obj["feature"]] = []
                ref = f"{split[1]}:{split[4][:-5]}"
                configured_feature_refs[obj["feature"]].append(ref)
            if len(split) == 5 and split[0] == "data" and split[2] == "worldgen" and split[3] == "configured_feature" and split[4].endswith(".json"):
                print(f"\tScanning {entry}")
                with zfo.open(entry) as f:
                    obj = json.loads(f.read().replace(b"minecraft:chain", b"minecraft:iron_chain")) # workaround tectonic
                if obj["type"] != "minecraft:random_patch":
                    continue
                ref = f"{split[1]}:{split[4][:-5]}"
                configured_feature_objs[ref] = obj

def v21dot1_v21dot2(in_file, out_file):
    with zipfile.ZipFile(in_file, mode="r") as zfo:
        with zipfile.ZipFile(out_file, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for entry in zfo.namelist():
                if entry.startswith("data/minecraft/worldgen/biome/") and entry.endswith(".json"):
                    print(f"Upgrading {entry}")
                    with zfo.open(entry) as f:
                        obj = json.load(f)

                    if 'carvers' in obj:
                        obj['carvers'] = obj['carvers']['air']

                    with zf.open(entry, "w") as f:
                        f.write(json.dumps(obj, indent=2).encode("UTF-8"))
                else:
                    with zfo.open(entry) as of:
                        with zf.open(entry, "w") as f:
                            f.write(of.read())

def v21dot3_v21dot4(in_file, out_file):
    with zipfile.ZipFile(in_file, mode="r") as zfo:
        with zipfile.ZipFile(out_file, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for entry in zfo.namelist():
                if entry.startswith("data/minecraft/worldgen/biome/") and entry.endswith(".json"):
                    print(f"Upgrading {entry}")
                    with zfo.open(entry) as f:
                        obj = json.load(f)

                    if "music" in obj["effects"]:
                        musicobj = obj["effects"]["music"]
                        obj["effects"]["music"] = [{"data": musicobj, "weight": 1}]
                        obj["effects"]["music_volume"] = 1.0

                    with zf.open(entry, "w") as f:
                        f.write(json.dumps(obj, indent=2).encode("UTF-8"))
                else:
                    with zfo.open(entry) as of:
                        with zf.open(entry, "w") as f:
                            f.write(of.read())

def v21dot6_v21dot7(in_file, out_file):
    mcmeta_zip_url = "https://github.com/misode/mcmeta/archive/0cf46a773e941afde9062cac2412096e40c6343b.zip"
    mcmeta_zip = "mcmeta_data_1_21_7.zip"

    if not os.path.isfile(mcmeta_zip):
        print("Downloading mcmeta data for 1.21.7")
        urllib.request.urlretrieve(mcmeta_zip_url, mcmeta_zip)

    with zipfile.ZipFile(mcmeta_zip, mode="r") as mcmeta:
        with zipfile.ZipFile(in_file, mode="r") as zfo:
            with zipfile.ZipFile(out_file, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
                for entry in zfo.namelist():
                    if entry.startswith("data/minecraft/worldgen/biome/") and entry.endswith(".json"):
                        print(f"Upgrading {entry}")
                        with zfo.open(entry) as f:
                            obj = json.load(f)

                        if "features" in obj:
                            with mcmeta.open("mcmeta-0cf46a773e941afde9062cac2412096e40c6343b/" + entry, "r") as f:
                                newobj = json.load(f)
                            obj["features"] = newobj["features"]

                        with zf.open(entry, "w") as f:
                            f.write(json.dumps(obj, indent=2).encode("UTF-8"))
                    else:
                        with zfo.open(entry) as of:
                            with zf.open(entry, "w") as f:
                                f.write(of.read())

def v21dot8_v21dot9(in_file, out_file):
    with zipfile.ZipFile(in_file, mode="r") as zfo:
        with zipfile.ZipFile(out_file, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for entry in zfo.namelist():
                if entry == "pack.mcmeta":
                    print(f"Upgrading {entry}: nuking pack.supported_formats")
                    with zfo.open(entry) as f:
                        info = json.load(f)
                    if "supported_formats" in info["pack"]:
                        del info["pack"]["supported_formats"]
                    with zf.open(entry, "w") as f:
                        f.write(json.dumps(info, indent=2).encode("UTF-8"))
                elif entry.startswith("data/minecraft/worldgen/noise_settings/") and entry.endswith(".json"):
                    print(f"Upgrading {entry}")
                    with zfo.open(entry) as f:
                        settings = json.load(f)
                    if 'noise_router' not in settings:
                        print("noise_router not found")
                        continue
                    if 'initial_density_without_jaggedness' not in settings['noise_router']:
                        print("noise_router.initial_density_without_jaggedness not found")
                        continue
                    if 'noise' not in settings:
                        print("noise not found")
                        continue

                    orig = settings['noise_router']['initial_density_without_jaggedness']
                    del settings['noise_router']['initial_density_without_jaggedness']
                    settings['noise_router']['preliminary_surface_level'] = {
                        "type": "minecraft:find_top_surface",
                        "cell_height": int(settings['noise']['size_vertical']) * 4,
                        "density": {
                            "type": "minecraft:add",
                            "argument1": -0.390625,
                            "argument2": orig
                        },
                        "lower_bound": int(settings['noise']['min_y']),
                        "upper_bound": float(int(settings['noise']['height']) - int(settings['noise']['min_y']))
                    }

                    with zf.open(entry, "w") as f:
                        f.write(json.dumps(settings, indent=2).encode("UTF-8"))
                else:
                    with zfo.open(entry) as of:
                        with zf.open(entry, "w") as f:
                            data = of.read()
                            if b"minecraft:chain" in data:
                                print(f"Upgrading {entry}: minecraft:chain -> minecraft:iron_chain")
                                data = data.replace(b"minecraft:chain", b"minecraft:iron_chain")
                            f.write(data)

def v21dot10_v21dot11(in_file, out_file):
    mcmeta_zip_url = "https://github.com/misode/mcmeta/archive/3458455b4b4537db37d6251a6ace1eed98d025a9.zip"
    mcmeta_zip = "mcmeta_data_1_21_11.zip"

    if not os.path.isfile(mcmeta_zip):
        print("Downloading mcmeta data for 1.21.11")
        urllib.request.urlretrieve(mcmeta_zip_url, mcmeta_zip)

    with zipfile.ZipFile(mcmeta_zip, mode="r") as mcmeta:
        with zipfile.ZipFile(in_file, mode="r") as zfo:
            with zipfile.ZipFile(out_file, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
                for entry in zfo.namelist():
                    split = entry.split("/")
                    # print(split, len(split))
                    # if entry.startswith("data/minecraft/worldgen/biome/") and entry.endswith(".json"):
                    if (len(split) == 5) and (split[0] == "data") and (split[2] == "worldgen") and (split[3] == "biome") and split[4].endswith(".json"):
                        print(f"Upgrading {entry}")
                        with zfo.open(entry) as f:
                            obj = json.load(f)

                        if ("mcmeta-3458455b4b4537db37d6251a6ace1eed98d025a9/" + entry) in mcmeta.namelist():
                            with mcmeta.open("mcmeta-3458455b4b4537db37d6251a6ace1eed98d025a9/" + entry, "r") as f:
                                newobj = json.load(f)
                        else:
                            print("Warning: unable to find entry in mcmeta")
                            newobj = {}
                        if "attributes" in newobj:
                            obj["attributes"] = newobj["attributes"]
                        else:
                            obj["attributes"] = {}

                        if "fog_color" in obj["effects"]:
                            obj["attributes"]["minecraft:visual/fog_color"] = f'#{obj["effects"]["fog_color"]:06x}'
                            del obj["effects"]["fog_color"]
                        if "water_fog_color" in obj["effects"]:
                            obj["attributes"]["minecraft:visual/water_fog_color"] = f'#{obj["effects"]["water_fog_color"]:06x}'
                            del obj["effects"]["water_fog_color"]
                        if "sky_color" in obj["effects"]:
                            obj["attributes"]["minecraft:visual/sky_color"] = f'#{obj["effects"]["sky_color"]:06x}'
                            del obj["effects"]["sky_color"]
                        if "particle" in obj["effects"]:
                            orig_particle_obj = obj["effects"]["particle"]
                            new_particle_obj = {"particle": {"type": orig_particle_obj["options"]["type"]}, "probability": orig_particle_obj["probability"]}
                            obj["attributes"]["minecraft:visual/ambient_particles"] = [new_particle_obj]
                            del obj["effects"]["particle"]
                        if ("ambient_sound" in obj["effects"]) or ("mood_sound" in obj["effects"]) or "additions_sound" in obj["effects"]:
                            if not ("minecraft:audio/ambient_sounds" in obj["attributes"]):
                                obj["attributes"]["minecraft:audio/ambient_sounds"] = {}
                            soundobj = obj["attributes"]["minecraft:audio/ambient_sounds"]
                            if "ambient_sound" in obj["effects"]:
                                soundobj["loop"] = obj["effects"]["ambient_sound"]
                                del obj["effects"]["ambient_sound"]
                            if "mood_sound" in obj["effects"]:
                                soundobj["mood"] = obj["effects"]["mood_sound"]
                                del obj["effects"]["mood_sound"]
                            if "additions_sound" in obj["effects"]:
                                soundobj["additions"] = obj["effects"]["additions_sound"]
                                del obj["effects"]["additions_sound"]
                        if "music" in obj["effects"]:
                            if not ("minecraft:audio/background_music" in obj["attributes"]):
                                obj["attributes"]["minecraft:audio/background_music"] = {}
                            if len(obj["effects"]["music"]) > 1:
                                print("Warning: only the first effects.music will be migrated")
                            if len(obj["effects"]["music"]) > 0:
                                obj["attributes"]["minecraft:audio/background_music"]["default"] = obj["effects"]["music"][0]["data"]
                            del obj["effects"]["music"]
                        if "music_volume" in obj["effects"]:
                            obj["attributes"]["minecraft:audio/music_volume"] = obj["effects"]["music_volume"]
                            del obj["effects"]["music_volume"]
                        if "water_color" in obj["effects"]:
                            obj["effects"]["water_color"] = f'#{obj["effects"]["water_color"]:06x}'
                        if "foliage_color" in obj["effects"]:
                            obj["effects"]["foliage_color"] = f'#{obj["effects"]["foliage_color"]:06x}'
                        if "dry_foliage_color" in obj["effects"]:
                            obj["effects"]["dry_foliage_color"] = f'#{obj["effects"]["dry_foliage_color"]:06x}'
                        if "grass_color" in obj["effects"]:
                            obj["effects"]["grass_color"] = f'#{obj["effects"]["grass_color"]:06x}'

                        with zf.open(entry, "w") as f:
                            f.write(json.dumps(obj, indent=2).encode("UTF-8"))
                    # elif entry.startswith("data/minecraft/dimension_type/") and entry.endswith(".json"):
                    elif len(split) == 4 and split[0] == "data" and split[2] == "dimension_type" and split[3].endswith(".json"):
                        print(f"Upgrading {entry}")
                        with zfo.open(entry) as f:
                            obj = json.load(f)

                        if ("mcmeta-3458455b4b4537db37d6251a6ace1eed98d025a9/" + entry) in mcmeta.namelist():
                            with mcmeta.open("mcmeta-3458455b4b4537db37d6251a6ace1eed98d025a9/" + entry, "r") as f:
                                newobj = json.load(f)
                        else:
                            print("Warning: unable to find entry in mcmeta")
                            newobj = {}
                        if "attributes" in newobj:
                            obj["attributes"] = newobj["attributes"]
                        else:
                            obj["attributes"] = {}
                        if "skybox" in newobj:
                            obj["skybox"] = newobj["skybox"]
                        if "timelines" in newobj:
                            obj["timelines"] = newobj["timelines"]

                        if "ultrawarm" in obj:
                            if obj["ultrawarm"]:
                                obj["attributes"]["minecraft:gameplay/water_evaporates"] = True
                                obj["attributes"]["minecraft:gameplay/fast_lava"] = True
                                obj["attributes"]["minecraft:visual/default_dripstone_particle"] = {"type": "minecraft:dripping_dripstone_lava"}
                            del obj["ultrawarm"]
                        if "bed_works" in obj:
                            if obj["bed_works"]:
                                obj["attributes"]["minecraft:gameplay/bed_rule"] = {
                                    "can_set_spawn": "always",
                                    "can_sleep": "when_dark",
                                    "error_message": {
                                        "translate": "block.minecraft.bed.no_sleep"
                                    }
                                }
                            else:
                                obj["attributes"]["minecraft:gameplay/bed_rule"] = {
                                    "can_set_spawn": "never",
                                    "can_sleep": "never",
                                    "explodes": True
                                }
                            del obj["bed_works"]
                        if "respawn_anchor_works" in obj:
                            obj["attributes"]["minecraft:gameplay/respawn_anchor_works"] = obj["respawn_anchor_works"]
                            del obj["respawn_anchor_works"]
                        if "cloud_height" in obj:
                            obj["attributes"]["minecraft:visual/cloud_height"] = obj["cloud_height"]
                            del obj["cloud_height"]
                        if "piglin_safe" in obj:
                            obj["attributes"]["minecraft:gameplay/piglins_zombify"] = not obj["piglin_safe"]
                            del obj["piglin_safe"]
                        if "has_raids" in obj:
                            obj["attributes"]["minecraft:gameplay/can_start_raid"] = obj["has_raids"]
                            del obj["has_raids"]
                        if "natural" in obj:
                            obj["attributes"]["minecraft:gameplay/nether_portal_spawns_piglin"] = obj["natural"]
                            del obj["natural"]
                        if "effects" in obj:
                            if obj["effects"] == "minecraft:nether":
                                obj["skybox"] = "none"
                                obj["cardinal_light"] = "nether"
                            elif obj["effects"] == "minecraft:overworld":
                                obj["skybox"] = "overworld"
                                obj["cardinal_light"] = "default"
                            elif obj["effects"] == "minecraft:end":
                                obj["skybox"] = "end"
                                obj["cardinal_light"] = "default"
                            del obj["effects"]
                        if "fixed_time" in obj:
                            obj["has_fixed_time"] = True
                            del obj["fixed_time"]

                        with zf.open(entry, "w") as f:
                            f.write(json.dumps(obj, indent=2).encode("UTF-8"))
                    else:
                        with zfo.open(entry) as of:
                            with zf.open(entry, "w") as f:
                                f.write(of.read())

def v21dot11_v26dot1(in_file, out_file):
    mcmeta_zip_url = "https://github.com/misode/mcmeta/archive/96c9ff11edcb485405c679132797eba82f2f6164.zip"
    mcmeta_zip = "mcmeta_data_26_1_pre_2.zip"

    if not os.path.isfile(mcmeta_zip):
        print("Downloading mcmeta data for 26.1-pre-2")
        urllib.request.urlretrieve(mcmeta_zip_url, mcmeta_zip)

    mcmeta_old_zip_url = "https://github.com/misode/mcmeta/archive/3458455b4b4537db37d6251a6ace1eed98d025a9.zip"
    mcmeta_old_zip = "mcmeta_data_1_21_11.zip"

    if not os.path.isfile(mcmeta_old_zip):
        print("Downloading mcmeta data for 1.21.11")
        urllib.request.urlretrieve(mcmeta_old_zip_url, mcmeta_old_zip)

    read_classpath(mcmeta_old_zip)
    for arg in sys.argv[1:]:
        if os.path.isfile(arg) and arg.lower().endswith('.zip'):
            read_classpath(arg)

    print(f"Read {len(configured_feature_refs)} configured feature refs, {len(configured_feature_objs)} configured feature objs")
    # print(configured_feature_refs)

    with zipfile.ZipFile(mcmeta_zip, mode="r") as mcmeta:
        with zipfile.ZipFile(in_file, mode="r") as zfo:
            with zipfile.ZipFile(out_file, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
                for entry in zfo.namelist():
                    split = entry.split("/")
                    # print(split, len(split))
                    while len(split) > 0 and split[0] != "data":
                        split = split[1:]
                    rejoined = "/".join(split)
                    if len(split) == 4 and split[0] == "data" and split[2] == "dimension_type" and split[3].endswith(".json"):
                        print(f"Upgrading {entry}")
                        with zfo.open(entry) as f:
                            obj = json.load(f)

                        if ("mcmeta-96c9ff11edcb485405c679132797eba82f2f6164/" + rejoined) in mcmeta.namelist():
                            with mcmeta.open("mcmeta-96c9ff11edcb485405c679132797eba82f2f6164/" + rejoined, "r") as f:
                                newobj = json.load(f)
                        else:
                            print("Warning: unable to find entry in mcmeta")
                            newobj = {}

                        if "attributes" in newobj: # optional field
                            if "minecraft:visual/block_light_tint" in newobj["attributes"]:
                                obj["attributes"]["minecraft:visual/block_light_tint"] = newobj["attributes"]["minecraft:visual/block_light_tint"]
                            if "minecraft:visual/ambient_light_color" in newobj["attributes"]:
                                obj["attributes"]["minecraft:visual/ambient_light_color"] = newobj["attributes"]["minecraft:visual/ambient_light_color"]
                            if "minecraft:visual/night_vision_color" in newobj["attributes"]:
                                obj["attributes"]["minecraft:visual/night_vision_color"] = newobj["attributes"]["minecraft:visual/night_vision_color"]

                        if "has_ender_dragon_fight" in newobj:
                            obj["has_ender_dragon_fight"] = newobj["has_ender_dragon_fight"]
                        else:
                            obj["has_ender_dragon_fight"] = False

                        with zf.open(entry, "w") as f:
                            f.write(json.dumps(obj, indent=2).encode("UTF-8"))
                    elif len(split) == 5 and split[0] == "data" and split[2] == "worldgen" and split[3] == "configured_feature" and split[4].endswith(".json"):
                        print(f"Upgrading {entry}")
                        with zfo.open(entry) as f:
                            obj = json.load(f)

                        # unwrap `random_patch`es
                        while obj["type"] == "minecraft:random_patch":
                            obj = obj["config"]["feature"]
                            if "placement" in obj:
                                obj = obj["feature"]

                        with zf.open(entry, "w") as f:
                            f.write(json.dumps(obj, indent=2).encode("UTF-8"))
                    elif len(split) == 5 and split[0] == "data" and split[2] == "worldgen" and split[3] == "placed_feature" and split[4].endswith(".json"):
                        print(f"Upgrading {entry}")
                        with zfo.open(entry) as f:
                            obj = json.load(f)

                        if obj["feature"] in configured_feature_objs:
                            cfobj = copy.deepcopy(configured_feature_objs[obj["feature"]])
                            while cfobj["type"] == "minecraft:random_patch":
                                obj["placement"].append({"type": "minecraft:count", "count": cfobj["config"]["tries"]})
                                obj["placement"].append({
                                    "type": "minecraft:random_offset",
                                    "xz_spread": {
                                        "type": "minecraft:trapezoid",
                                        "max": cfobj["config"]["xz_spread"],
                                        "min": -cfobj["config"]["xz_spread"],
                                        "plateau": 0
                                    },
                                    "y_spread": {
                                        "type": "minecraft:trapezoid",
                                        "max": cfobj["config"]["y_spread"],
                                        "min": -cfobj["config"]["y_spread"],
                                        "plateau": 0
                                    }
                                })
                                cfobj = cfobj["config"]["feature"]
                                if "placement" in cfobj:
                                    for placement in cfobj["placement"]:
                                        obj["placement"].append(placement)
                                    cfobj = cfobj["feature"]

                        with zf.open(entry, "w") as f:
                            f.write(json.dumps(obj, indent=2).encode("UTF-8"))
                    elif entry == "pack.mcmeta":
                        print(f"Upgrading {entry}")
                        with zfo.open(entry) as f:
                            info = json.load(f)
                        if "supported_formats" in info["pack"]:
                            info["pack"]["supported_formats"] = [info["pack"]["supported_formats"][0], 1000]
                        if "max_format" in info["pack"]:
                            info["pack"]["max_format"] = 1000
                        if "overlays" in info:
                            for entry_elem in info["overlays"]["entries"]:
                                if "formats" in entry_elem:
                                    entry_elem["formats"] = [entry_elem["formats"][0], 1000]
                                if "max_format" in entry_elem:
                                    entry_elem["max_format"] = 1000
                        with zf.open(entry, "w") as f:
                            f.write(json.dumps(info, indent=2).encode("UTF-8"))
                    else:
                        with zfo.open(entry) as of:
                            with zf.open(entry, "w") as f:
                                f.write(of.read())

dispatch = {
    1: v21dot1_v21dot2,
    2: v21dot3_v21dot4,
    3: v21dot6_v21dot7,
    4: v21dot8_v21dot9,
    5: v21dot10_v21dot11,
    6: v21dot11_v26dot1
}

labels = {
    1: '1.21/1.21.1',
    2: '1.21.2/1.21.3',
    3: '1.21.4/1.21.5/1.21.6',
    4: '1.21.7/1.21.8',
    5: '1.21.9/1.21.10',
    6: '1.21.11',
    7: '26.1'
}

def print_usage():
    print('Usage: main.py <filename> <init_stage> <final_stage>')
    print('Stages:')
    print('  1: 1.21/1.21.1')
    print('  2: 1.21.2/1.21.3')
    print('  3: 1.21.4/1.21.5/1.21.6')
    print('  4: 1.21.7/1.21.8')
    print('  5: 1.21.9/1.21.10')
    print('  6: 1.21.11')
    print('  7: 26.1')


def run_upgrade(in_file, out_file, init_ver, final_ver):
    if init_ver < 1 or init_ver > 6:
        print('Invalid initial ver')
        return False
    if final_ver < 2 or final_ver > 7:
        print('Invalid final ver')
        return False
    if final_ver <= init_ver:
        print('How tf am I supposed to upgade to an older version or the same version ... IT\'S UPGRADE bruh.')
        return False

    configured_feature_refs.clear()
    configured_feature_objs.clear()

    current_file = in_file
    current_stage = init_ver
    temp_files = []
    failed = False

    try:
        while current_stage < final_ver:
            action = dispatch.get(current_stage)
            next_stage = current_stage + 1
            if action is None:
                failed = True
                break

            if next_stage == final_ver:
                next_file = out_file
            else:
                next_file = f"{os.path.splitext(out_file)[0]}_tmp_{next_stage}.zip"
                temp_files.append(next_file)

            print(f'Running {labels[current_stage]} -> {labels[next_stage]}')
            action(current_file, next_file)
            current_file = next_file
            current_stage = next_stage
    except Exception as exc:
        print(f'Upgrade failed: {exc}')
        failed = True
    finally:
        for tmp in temp_files:
            if os.path.isfile(tmp):
                try:
                    os.remove(tmp)
                except OSError:
                    pass

    if failed:
        return False

    print(f'Upgrade completed: {out_file}')
    return True


if len(sys.argv) > 1:
    if len(sys.argv) != 4:
        print_usage()
        sys.exit(1)

    in_file = sys.argv[1]
    try:
        init_ver = int(sys.argv[2])
        final_ver = int(sys.argv[3])
    except ValueError:
        print_usage()
        sys.exit(1)

    if not os.path.isfile(in_file):
        print(f'Input file not found: {in_file}')
        sys.exit(1)

    out_file = f"{os.path.splitext(in_file)[0]}_{labels[final_ver].replace('.', '_').replace('/', '_')}.zip"
    ok = run_upgrade(in_file, out_file, init_ver, final_ver)
    sys.exit(0 if ok else 1)

while True:
    # cls()

    print('Select the initial datapack version:')
    print('1. 1.21/1.21.1')
    print('2. 1.21.2/1.21.3')
    print('3. 1.21.4/1.21.5/1.21.6')
    print('4. 1.21.7/1.21.8')
    print('5. 1.21.9/1.21.10')
    print('6. 1.21.11')
    try:
        init_ver = int(input('Enter the number corresponding to the version: '))
    except ValueError:
        continue

    # cls()

    print('Select the final datapack version:')
    print('1. 1.21.2/1.21.3')
    print('2. 1.21.4/1.21.5/1.21.6')
    print('3. 1.21.7/1.21.8')
    print('4. 1.21.9/1.21.10')
    print('5. 1.21.11')
    print('6. 26.1')
    try:
        final_ver0 = int(input('Enter the number corresponding to the version: '))
    except ValueError:
        continue

    final_ver = final_ver0 + 1

    # cls()

    in_file = filedialog.askopenfilename(title="Select the datapack zip file to upgrade")

    if not in_file:
        print('No file selected')
        continue

    out_file = filedialog.asksaveasfilename(
        title='Save upgraded datapack as',
        defaultextension='.zip',
        initialfile=f"{os.path.splitext(os.path.basename(in_file))[0]}_{labels[final_ver].replace('.', '_').replace('/', '_')}.zip",
        filetypes=[('Zip files', '*.zip'), ('All files', '*.*')]
    )

    if not out_file:
        print('No output file selected')
        continue

    st = run_upgrade(in_file, out_file, init_ver, final_ver)
    sys.exit(0 if st else 1)
