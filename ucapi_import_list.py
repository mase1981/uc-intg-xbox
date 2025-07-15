from ucapi import EntityTypes

for entity_type in EntityTypes:
    print(entity_type.name, "=", entity_type.value)

# Expected Output:
# MEDIA_PLAYER = media_player
# LIGHT = light
# ...and so on