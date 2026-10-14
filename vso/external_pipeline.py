"""Read-only discovery of separately installed optional AGPL workflow runtime.

OpenMontage remains a distinct, licensed software installation. Nothing is
vendored or executed by this adapter. Do not claim its providers are usable.
"""
import os
import re
from pathlib import Path


def status():
    root=Path(os.environ.get("VSO_MONTAGE_ROOT","/opt/vegas-social-os-integrations/openmontage"))
    try:
        if not root.is_dir():return {"installed":False,"source_present":False,"execution_verified":False,
                                    "next":"Install optional external runtime separately; existing Vegas tools stay functional."}
        license_text=(root/"LICENSE").read_text()[:160]
        if "GNU AFFERO GENERAL PUBLIC LICENSE" not in license_text:
            raise ValueError("External workflow checkout does not contain its required AGPL license")
        manifests=root/"pipeline_defs"
        names=[p.stem for p in manifests.iterdir() if p.is_file() and p.suffix in (".yml",".yaml") and re.fullmatch(r"[\w-]{1,80}",p.stem)]
        return {"source_present":True,"installed":False,"execution_verified":False,
                "manifest_names":sorted(names),
                "provider_keys_verified":False,"runtime_dependencies_verified":False,
                "license":"AGPLv3; external source and notices retained, not merged into Vegas",
                "integration":"External source catalogue only; native Vegas workflows execute independently. No video generation from external source was run."}
    except (OSError,ValueError) as e:
        return {"source_present":False,"installed":False,"execution_verified":False,"error":str(e)[:200]}
