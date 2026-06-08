import math

# 6-sensor insole layout (pins 1-6 → values[0-5])
# x: 0.0=medial(inner), 1.0=lateral(outer)
# y: 0.0=heel, 1.0=toe
_SENSOR_POSITIONS = [
    (0.2, 0.9),  # 0: forefoot-medial
    (0.5, 0.9),  # 1: forefoot-center
    (0.8, 0.9),  # 2: forefoot-lateral
    (0.2, 0.1),  # 3: heel-medial
    (0.5, 0.1),  # 4: heel-center
    (0.8, 0.1),  # 5: heel-lateral
]

_FRONT_IDX = [0, 1, 2]
_REAR_IDX = [3, 4, 5]


def analyze_heart_rate(hr_data: list[dict]) -> dict:
    if not hr_data:
        return {"available": False}

    bpms = [int(r["bpm"]) for r in hr_data]
    n = len(bpms)
    avg = sum(bpms) / n
    max_bpm = max(bpms)
    min_bpm = min(bpms)
    std = math.sqrt(sum((b - avg) ** 2 for b in bpms) / n)

    # 심박수 구간 (최대 심박수 대비 %)
    def _zone(bpm: int) -> int:
        pct = bpm / max_bpm
        if pct < 0.60:
            return 1
        if pct < 0.70:
            return 2
        if pct < 0.80:
            return 3
        if pct < 0.90:
            return 4
        return 5

    zone_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for b in bpms:
        zone_counts[_zone(b)] += 1
    zones = {k: round(v / n * 100, 1) for k, v in zone_counts.items()}

    risks = []
    if avg > 180:
        risks.append("sustained_high_heart_rate")
    if min_bpm < 40:
        risks.append("bradycardia")
    if std > 25:
        risks.append("irregular_heart_rate")

    return {
        "available": True,
        "avg": round(avg, 1),
        "max": max_bpm,
        "min": min_bpm,
        "std": round(std, 1),
        "samples": n,
        "zones": zones,
        "risks": risks,
    }


def _foot_stats(vals: list[int]) -> dict:
    """단일 발의 전후 균형, CoP 계산."""
    total = sum(vals)
    if total == 0:
        return {
            "frontBackBalance": {"front": 50.0, "rear": 50.0},
            "cop": {"x": 0.5, "y": 0.5},
        }

    front = sum(vals[i] for i in _FRONT_IDX)
    rear = sum(vals[i] for i in _REAR_IDX)
    cop_x = sum(vals[i] * _SENSOR_POSITIONS[i][0] for i in range(6)) / total
    cop_y = sum(vals[i] * _SENSOR_POSITIONS[i][1] for i in range(6)) / total

    return {
        "frontBackBalance": {
            "front": round(front / total * 100, 1),
            "rear": round(rear / total * 100, 1),
        },
        "cop": {"x": round(cop_x, 3), "y": round(cop_y, 3)},
    }


def analyze_foot_pressure(fp_data: dict) -> dict:
    left = fp_data.get("left")
    right = fp_data.get("right")

    if not left and not right:
        return {"available": False, "risks": []}

    result: dict = {"available": True, "risks": [], "footAnalysis": {}}

    if left and len(left) == 6:
        result["footAnalysis"]["left"] = _foot_stats(left)
    if right and len(right) == 6:
        result["footAnalysis"]["right"] = _foot_stats(right)

    # 좌우 균형
    if left and right:
        lt = sum(left)
        rt = sum(right)
        grand = lt + rt
        if grand > 0:
            lp = round(lt / grand * 100, 1)
            rp = round(rt / grand * 100, 1)
        else:
            lp = rp = 50.0
        result["leftRightBalance"] = {"left": lp, "right": rp}
        if abs(lp - 50.0) > 10:
            result["risks"].append("left_right_imbalance")

    # 전후 불균형 위험
    for side in ("left", "right"):
        stats = result["footAnalysis"].get(side)
        if stats:
            fb = stats["frontBackBalance"]
            if fb["front"] > 65 or fb["rear"] > 65:
                result["risks"].append(f"{side}_front_back_imbalance")

    return result


def detect_risks(hr_analysis: dict, fp_analysis: dict) -> list[dict]:
    _HR_LABELS = {
        "sustained_high_heart_rate": (
            "심박수 과부하",
            "심박수가 지속적으로 높았습니다. 훈련 강도를 낮추거나 충분한 회복을 취하세요.",
        ),
        "bradycardia": (
            "심박수 이상 저하",
            "심박수가 비정상적으로 낮았습니다. 의료 전문가 상담을 권장합니다.",
        ),
        "irregular_heart_rate": (
            "심박수 불규칙",
            "심박수 변동 폭이 크게 나타났습니다. 컨디션을 확인하세요.",
        ),
    }
    _FP_LABELS = {
        "left_right_imbalance": (
            "좌우 하중 불균형",
            "좌우 발 하중 차이가 10% 이상입니다. 균형 훈련을 권장합니다.",
        ),
        "left_front_back_imbalance": (
            "왼발 전후 불균형",
            "왼발의 전후 하중 분포가 불균형합니다.",
        ),
        "right_front_back_imbalance": (
            "오른발 전후 불균형",
            "오른발의 전후 하중 분포가 불균형합니다.",
        ),
    }

    risks = []
    for code in hr_analysis.get("risks", []):
        label, desc = _HR_LABELS.get(code, (code, ""))
        risks.append({"type": "heart_rate", "code": code, "label": label, "description": desc})

    for code in fp_analysis.get("risks", []):
        label, desc = _FP_LABELS.get(code, (code, ""))
        risks.append({"type": "foot_pressure", "code": code, "label": label, "description": desc})

    return risks
