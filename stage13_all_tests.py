from eta_confidence import ETAConfidence
from delay_impact import DelayImpactAnalyzer
from operational_alerts import OperationalAlertGenerator
from passenger_alerts import PassengerAlertGenerator
from stage13_pipeline import Stage13Pipeline


def test_13_1():
    confidence = ETAConfidence()

    normal = confidence.calculate(10, 2, 15)
    assert normal["confidence_score"] == 100
    assert normal["confidence_level"] == "HIGH"

    uncertain = confidence.calculate(600, 150, 200)
    assert uncertain["confidence_score"] < 60
    assert uncertain["confidence_level"] == "LOW"

    try:
        confidence.calculate(-1, 2, 15)
        assert False
    except ValueError:
        pass


def test_13_2():
    analyzer = DelayImpactAnalyzer()

    result = analyzer.analyze(17, 30, 10)

    assert result["predicted_delay"] == 30.0
    assert result["delay_change"] == 13.0
    assert result["severity"] == "HIGH"
    assert result["trend"] == "WORSENING"
    assert result["route_impact"] == "MEDIUM_TERM"

    improving = analyzer.analyze(40, 20, 3)
    assert improving["trend"] == "IMPROVING"


def test_13_3():
    generator = OperationalAlertGenerator()

    impact = {
        "current_delay": 17.0,
        "predicted_delay": 80.0,
        "delay_change": 63.0,
        "severity": "CRITICAL",
        "trend": "WORSENING",
        "route_impact": "LONG_ROUTE",
    }

    confidence = {
        "confidence_score": 55,
        "confidence_level": "LOW",
    }

    alerts = generator.generate(impact, confidence)
    types = {alert["type"] for alert in alerts}

    assert "CRITICAL_DELAY" in types
    assert "DELAY_WORSENING" in types
    assert "LOW_ETA_CONFIDENCE" in types


def test_13_4():
    generator = PassengerAlertGenerator()

    result = generator.generate(
        train_number="12303",
        destination_station="BZL",
        predicted_eta="2024-09-26 08:27:55",
        remaining_minutes=10.93,
        delay_status="DELAYED",
        confidence_level="HIGH",
    )

    assert result["train_number"] == "12303"
    assert result["destination_station"] == "BZL"
    assert result["remaining_minutes"] == 10.93
    assert result["delay_status"] == "DELAYED"
    assert "12303" in result["message"]
    assert "BZL" in result["message"]


def test_13_5():
    pipeline = Stage13Pipeline()

    # Representative structure produced by the existing
    # Dynamic ETA Engine / predictor layer.
    eta_result = {
        "eta": "2024-09-26 08:27:55",
        "remaining_minutes": 10.93,
        "stations_ahead": 2,
        "future_arrival_delay": 30.0,
    }

    result = pipeline.process(
        train_number="12303",
        destination_station="BZL",
        eta_result=eta_result,
        current_delay=17,
        delay_status="DELAYED",
    )

    assert result["train_number"] == "12303"
    assert result["destination_station"] == "BZL"

    assert result["confidence"]["confidence_level"] == "HIGH"

    assert result["delay_impact"]["severity"] == "HIGH"
    assert result["delay_impact"]["trend"] == "WORSENING"

    alert_types = {
        alert["type"]
        for alert in result["operational_alerts"]
    }

    assert "HIGH_DELAY" in alert_types
    assert "DELAY_WORSENING" in alert_types

    passenger = result["passenger_information"]

    assert passenger["train_number"] == "12303"
    assert passenger["destination_station"] == "BZL"
    assert passenger["predicted_eta"] == "2024-09-26 08:27:55"


def main():
    print("=" * 60)
    print("STAGE 13 - OPERATIONAL INTELLIGENCE")
    print("=" * 60)

    print("\nSTAGE 13.1 - ETA CONFIDENCE")
    test_13_1()
    print("PASS")

    print("\nSTAGE 13.2 - DELAY IMPACT ANALYSIS")
    test_13_2()
    print("PASS")

    print("\nSTAGE 13.3 - OPERATIONAL ALERT GENERATION")
    test_13_3()
    print("PASS")

    print("\nSTAGE 13.4 - PASSENGER ALERT GENERATION")
    test_13_4()
    print("PASS")

    print("\nSTAGE 13.5 - END-TO-END OPERATIONAL INTELLIGENCE")
    test_13_5()
    print("PASS")

    print("\n" + "=" * 60)
    print("ALL STAGE 13 TESTS PASSED")
    print("STAGE 13: COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
