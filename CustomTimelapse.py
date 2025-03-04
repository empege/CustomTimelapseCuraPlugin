from ..Script import Script

class CustomTimelapse(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Custom timelapse",
            "key": "CustomTimelapse",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "activate_plugin":
                {
                    "label": "Enable plugin",
                    "description": "Select if you want the plugin to be active (allows you to desactivate without losing your configuration)",
                    "type": "bool",
                    "default_value": true
                },
                "first_gcode":
                {
                    "label": "GCODE for the first position(display position).",
                    "description": "GCODE to add before or after layer change.",
                    "type": "str",
                    "default_value": "G0 Y235"
                },
                "second_gcode":
                {
                    "label": "GCODE for the second position(trigger position).",
                    "description": "GCODE to add before or after layer change.",
                    "type": "str",
                    "default_value": "G0 X235"
                },
                "third_gcode":
                {
                    "label": "GCODE for the third position(pause position).",
                    "description": "GCODE to add before or after layer change.",
                    "type": "str",
                    "default_value": "G0 X225"
                },
                "enable_custom_return_speed":
                {
                    "label": "Specify a return speed",
                    "description": "Set the value below",
                    "type": "bool",
                    "default_value": false
                },
                "return_speed":
                {
                    "label": "return speed in mm/minutes",
                    "description": "return speed in mm/minute as for the F gcode parameter.",
                    "type": "int",
                    "unit": "mm/m",
                    "enabled": "enable_custom_return_speed"
                },
                "pause_length":
                {
                    "label": "Pause length",
                    "description": "How long to wait (in ms) after camera was triggered.",
                    "type": "int",
                    "default_value": 700,
                    "minimum_value": 0,
                    "unit": "ms"
                },
                "enable_retraction":
                {
                    "label": "Enable retraction",
                    "description": "Retract the filament before moving the head",
                    "type": "bool",
                    "default_value": true
                },
                "retraction_distance":
                {
                    "label": "Retraction distance",
                    "description": "How much to retract the filament.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 5,
                    "enabled": "enable_retraction"
                },
                "display_photo_number":
                {
                    "label": "Display current photo number",
                    "description": "Display the current photo number on the panel during the shots",
                    "type": "bool",
                    "default_value": false
                },
                "send_photo_command":
                {
                    "label": "Send camera command",
                    "description": "Send a customisable G-code command for compatible printers",
                    "type": "bool",
                    "default_value": false
                },
                "trigger_command":
                {
                    "label": "Trigger camera command",
                    "description": "Gcode command used to trigger camera.",
                    "type": "str",
                    "default_value": "M240",
                    "enabled": "send_photo_command"
                }
            }
        }"""
    # Note : This function and some other bits of code comes from PauseAtHeight.py
    ##  Get the X and Y values for a layer (will be used to get X and Y of the
    #   layer after the pause).
    def getNextXY(self, layer):
        lines = layer.split("\n")
        for line in lines:
            if self.getValue(line, "X") is not None and self.getValue(line, "Y") is not None:
                x = self.getValue(line, "X")
                y = self.getValue(line, "Y")
                return x, y
        return 0, 0

    def execute(self, data):
        activate_plugin = self.getSettingValueByKey("activate_plugin")
        first_gcode = self.getSettingValueByKey("first_gcode")
        second_gcode = self.getSettingValueByKey("second_gcode")
        third_gcode = self.getSettingValueByKey("third_gcode")
        pause_length = self.getSettingValueByKey("pause_length")
        enable_custom_return_speed = self.getSettingValueByKey("enable_custom_return_speed")
        return_speed = self.getSettingValueByKey("return_speed")
        enable_retraction = self.getSettingValueByKey("enable_retraction")
        retraction_distance = self.getSettingValueByKey("retraction_distance")
        display_photo_number = self.getSettingValueByKey("display_photo_number")
        send_photo_command = self.getSettingValueByKey("send_photo_command")
        trigger_command = self.getSettingValueByKey("trigger_command")

        for layerIndex, layer in enumerate(data):
            # Check that a layer is being printed
            lines = layer.split("\n")
            for line in lines:
                if ";LAYER:" in line:
                    index = data.index(layer)

                    next_layer = data[layerIndex + 1]
                    x, y = self.getNextXY(next_layer)

                    gcode_to_append = ""

                    if activate_plugin:
                        gcode_to_append += ";CustomTimelapse Begin\n"

                        if display_photo_number:
                            gcode_to_append += "M117 Taking photo " + str(layerIndex) + "...\n"

                        gcode_to_append += "; STEP 1 : retraction\n"
                        gcode_to_append += self.putValue(M = 83) + " ; switch to relative E values for any needed retraction\n"
                        if enable_retraction:
                            gcode_to_append += self.putValue(G = 1, F = 1800, E = -retraction_distance) + ";Retraction\n"
                        gcode_to_append += self.putValue(M = 82) + ";Switch back to absolute E values\n"

                        gcode_to_append += "; STEP 2 : Move the head up a bit\n"
                        gcode_to_append += self.putValue(G = 91) + ";Switch to relative positioning\n"
                        gcode_to_append += self.putValue(G = 0, Z = 1) + ";Move Z axis up a bit\n"
                        gcode_to_append += self.putValue(G = 90) + ";Switch back to absolute positioning\n"

                        gcode_to_append += "; STEP 3 : Move the head to \"display\" position and wait\n"
                        gcode_to_append += first_gcode + ";GCODE for the first position(display position)\n"
                        gcode_to_append += second_gcode + ";GCODE for the second position(trigger position)\n"
                        gcode_to_append += third_gcode + ";GCODE for the third position(pause position)\n"
                        gcode_to_append += self.putValue(M = 400) + ";Wait for moves to finish\n"
                        gcode_to_append += self.putValue(G = 4, P = pause_length) + ";Wait for camera\n"

                        gcode_to_append += "; STEP 4 : send photo trigger command if set\n"
                        if send_photo_command:
                            gcode_to_append += trigger_command + " ;Snap Photo\n"

                        # TODO skip steps 5 and 6 for the last layer
                        gcode_to_append += "; STEP 5 : Move the head back in its original place\n"
                        if enable_custom_return_speed:
                            gcode_to_append += self.putValue(G = 0, X = x, Y = y, F = return_speed) + "\n"
                        else:
                            gcode_to_append += self.putValue(G = 0, X = x, Y = y) + "\n"

                        gcode_to_append += "; STEP 6 : Move the head height back down\n"
                        gcode_to_append += self.putValue(G = 91) + ";Switch to relative positioning\n"
                        gcode_to_append += self.putValue(G = 0, Z = -1) + ";Restore Z axis position\n"
                        gcode_to_append += self.putValue(G = 90) + ";Switch back to absolute positioning\n"

                        gcode_to_append += ";CustomTimelapse End\n"


                    layer += gcode_to_append

                    data[index] = layer
                    break
        return data
