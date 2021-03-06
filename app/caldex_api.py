from aiohttp import web
import time
import json
import math
class CaldexApi:

    def __init__(self, services):
        self.data_svc = services.get('data_svc')
        self.auth_svc = services.get('auth_svc')

    async def export(self, request):
        await self.auth_svc.check_permissions(request)
        try:
            operation_filter = request.match_info.get('operation', '')
            criteria = None
            if operation_filter:
                criteria = dict(op_id = operation_filter)
            operations = await self.data_svc.explode_operation(criteria)  
            # Compute techniques
            abilities = dict()
            techniques = dict()
            for operation in operations:
                for phase in operation["adversary"]["phases"].values():
                    for ability in phase:
                        aKey = ability["id"]
                        if aKey not in abilities:
                            tKey = "{0}/{1}".format(ability["tactic"], ability["technique_id"])
                            abilities[aKey] = tKey
                            if tKey not in techniques:
                                techniques[tKey] = {"tactic": ability["tactic"], "techniqueID": ability["technique_id"], "enabled": False, "score": [0, 0]}
                for execution in operation["chain"]:
                    executed = execution["status"] >= 0
                    successful = execution["status"] == 0
                    if executed:
                        aKey = execution["ability"]
                        tKey = abilities[aKey]
                        technique = techniques[tKey]
                        technique["score"][0] += 1
                        if "enabled" in technique:
                            del technique["enabled"]
                            technique["color"] = "#00ff00"
                        if successful:
                            if "color" in technique:
                                del technique["color"]
                            technique["score"][1] += 1
            # Compute results
            for technique in techniques.values():
                technique["score"] = math.ceil(technique["score"][1] / max(technique["score"][0], 1) * 100)
            return web.json_response({
                    "version": "2.2",
                    "name": "Caldera Export",
                    "description": "Caldera Export on {}".format(time.strftime("%Y-%m-%d %H:%M")),
                    "domain": "mitre-enterprise",
                    "sorting": 3,
                    "techniques": list(techniques.values()),
                    "gradient": {
                            "colors": ["#bbff00", "#ffff00", "#ff0000"],
                            "minValue": 0,
                            "maxValue": 100,
                        },
                    "legendItems": [
                            {
                                "label": "Mitigated Techniques",
                                "color": "#00ff00",
                            },
                            {
                                "label": "Partially Vulnerable Techniques",
                                "color": "#ffff00"
                            },
                            {
                                "label": "Vulnerable Techniques",
                                "color": "#ff0000",
                            },
                            {
                                "label": "Unknown Techniques",
                                "color": "#ffffff",
                            },
                        ],
                    "selectTechniquesAcrossTactics": False,
                    "metadata": [
                            {
                                "name": "Get the source code!",
                                "value": "https://github.com/nviso-be/caldex",
                            },
                            {
                                "name": "Looking for an infosec job?",
                                "value": "https://www.nviso.eu/en/jobs",
                            },
                        ],
                })
        except Exception as e:
            return web.Response(body="Oops...: {}".format(repr(e)))
