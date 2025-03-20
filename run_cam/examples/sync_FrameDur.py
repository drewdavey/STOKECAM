#!/usr/bin/python


from picamera2 import Picamera2


def P_controller(Kp: float = 0.05, setpoint: float = 0, measurement: float = 0, output_limits=(-10000, 10000)):
    e = setpoint - measurement
    P = Kp * e

    output_value = P

    # output and limit if output_limits set
    lower, upper = output_limits
    if (upper is not None) and (output_value > upper):
        return upper
    elif (lower is not None) and (output_value < lower):
        return lower
    return output_value


if len(Picamera2.global_camera_info()) <= 1:
    print("SKIPPED (one camera)")
    quit()

# Primary (leads)
picam2a = Picamera2(0)
# need buffer_count > 1 because if a frame is skipped, there will be a jump in SensorTimestamp due to dropped frame which messes with the control
config2a = picam2a.create_still_configuration(controls={"FrameRate": 25}, buffer_count=3)
picam2a.configure(config2a)

# Secondary (follows)
picam2b = Picamera2(1)
# need buffer_count > 1 because if a frame is skipped, there will be a jump in SensorTimestamp due to dropped frame which messes with the control
config2b = picam2b.create_still_configuration(controls={"FrameRate": 25}, buffer_count=3)
picam2b.configure(config2b)


picam2a.start()
picam2b.start()

print("Press Ctrl+C to exit")
try:
    while True:
        metadata_picam2a = picam2a.capture_metadata()
        metadata_picam2b = picam2b.capture_metadata()

        timestamp_picam2a = metadata_picam2a["SensorTimestamp"] / 1000  #  convert ns to µs because all other values are in µs
        timestamp_picam2b = metadata_picam2b["SensorTimestamp"] / 1000  #  convert ns to µs because all other values are in µs
        timestamp_delta = timestamp_picam2b - timestamp_picam2a

        controller_output_frameduration_delta = int(P_controller(0.05, 0, timestamp_delta, (-10000, 10000)))
        control_out_frameduration = int(metadata_picam2a["FrameDuration"] + controller_output_frameduration_delta)  # sync to a, so use that for ref

        print("Cam A: SensorTimestamp: ", timestamp_picam2a, " FrameDuration: ", metadata_picam2a["FrameDuration"])
        print("Cam B: SensorTimestamp: ", timestamp_picam2b, " FrameDuration: ", metadata_picam2b["FrameDuration"])
        print("SensorTimestampDelta: ", round(timestamp_delta / 1000, 1), "ms")
        print("FrameDurationDelta: ", controller_output_frameduration_delta, "new FrameDurationLimit: ", control_out_frameduration)

        with picam2b.controls as ctrl:
            # set new FrameDurationLimits based on P_controller output.
            ctrl.FrameDurationLimits = (control_out_frameduration, control_out_frameduration)

except KeyboardInterrupt:
    print("got Ctrl+C, exiting")


picam2a.stop()
picam2b.stop()
