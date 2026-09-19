import datetime
import math

from app.pipeline.time_sync import SensorStream, ecef_to_geodetic, geodetic_to_ecef, quaternion_slerp


def test_ppph_time_parsing():
    # Verify PPPH-UAV GPS week+seconds to Unix UTC parsing
    # week=2234, sec=552471.663062 -> 1667640453.663062
    gps_epoch = datetime.datetime(1980, 1, 6, 0, 0, 0, tzinfo=datetime.timezone.utc)
    week = 2234
    sec = 552471.663062
    dt = gps_epoch + datetime.timedelta(weeks=week, seconds=sec)
    leap_seconds = 18
    unix_ts = dt.timestamp() - leap_seconds

    assert math.isclose(unix_ts, 1667640453.663062, abs_tol=1e-5)


def test_sensor_stream_monotonicity():
    stream = SensorStream("test")
    stream.add_samples(
        [
            (1.0, 1),
            (2.0, 2),
            (1.5, 3),  # Backward
            (3.0, 4),
        ]
    )
    stats = stream.get_stats()
    assert not stats["source_was_monotonic"]
    assert stats["backward_count"] == 1
    assert stats["rows_reordered"]

    # Should be sorted
    assert stream.samples[0][0] == 1.0
    assert stream.samples[1][0] == 1.5
    assert stream.samples[2][0] == 2.0
    assert stream.samples[3][0] == 3.0


def test_sensor_stream_duplicates():
    stream = SensorStream("test", policy="KEEP_FIRST")
    stream.add_samples([(1.0, 1), (1.0, 2), (2.0, 3)])
    stats = stream.get_stats()
    assert stats["duplicate_count"] == 1
    assert len(stream.samples) == 2
    assert stream.samples[0][2] == 1  # Kept first


def test_geodetic_cartesian_roundtrip():
    lat, lon, alt = 47.3843571, 8.5451784, 464.91
    x, y, z = geodetic_to_ecef(lat, lon, alt)
    lat2, lon2, alt2 = ecef_to_geodetic(x, y, z)
    assert math.isclose(lat, lat2, abs_tol=1e-6)
    assert math.isclose(lon, lon2, abs_tol=1e-6)
    assert math.isclose(alt, alt2, abs_tol=1e-3)


def test_quaternion_slerp():
    q1 = (1.0, 0.0, 0.0, 0.0)
    q2 = (0.0, 1.0, 0.0, 0.0)  # 180 degree rotation around X
    # Midpoint should be w=0.707, x=0.707
    qm = quaternion_slerp(q1, q2, 0.5)
    assert math.isclose(qm[0], 0.70710678, abs_tol=1e-5)
    assert math.isclose(qm[1], 0.70710678, abs_tol=1e-5)


def test_quaternion_sign_ambiguity():
    q1 = (1.0, 0.0, 0.0, 0.0)
    q2 = (-1.0, 0.0, 0.0, 0.0)  # Same rotation, negative sign
    qm = quaternion_slerp(q1, q2, 0.5)
    # Should resolve dot product < 0 and take shortest path (distance 0)
    assert math.isclose(qm[0], 1.0, abs_tol=1e-5)


def test_linear_interpolation_limits():
    stream = SensorStream("test")
    stream.add_samples([(1.0, (10,)), (2.0, (20,))])
    # Exact
    stat, dt, val = stream.interpolate(1.0, 5.0)
    assert stat == "EXACT"
    assert val == (10,)

    # Interp
    stat, dt, val = stream.interpolate(1.5, 5.0)
    assert stat == "INTERPOLATED"
    assert val == (15.0,)

    # Outside range (No extrapolation)
    stat, dt, val = stream.interpolate(2.5, 5.0)
    assert stat == "OUTSIDE_SENSOR_RANGE"

    # Gap too large
    stat, dt, val = stream.interpolate(1.5, 0.1)
    assert stat == "GAP_TOO_LARGE"
