# confusion_rules.py

CONFUSION_UPGRADE_RULES = {
    "symbol": {
        "threshold": 2,
        "next": "quantifier",
    },
    "quantifier": {
        "threshold": 2,
        "next": "dependency",
    },
    "dependency": {
        "threshold": 2,
        "next": "proof_logic",
    },
}
