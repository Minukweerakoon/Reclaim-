# Behavior Detection Logic Extraction

This document describes the behavior detection logic extracted from the original YOLOv8 and YOLOv11 notebooks and implemented in the ML service.

## Source

The behavior detection logic was extracted from:
- **YOLOv8.ipynb** - Cell 13 (main implementation)
- **YOLOv11.ipynb** - Cell 9 (similar implementation)

## Implemented Behaviors

### 1. Unattended Bag Detection

**Logic:**
- Track each bag's center position
- For each bag, find the nearest person
- Calculate distance between bag center and person center
- If distance > `OWNER_MAX_DIST` pixels:
  - Start/continue timer for owner absence
  - If timer >= `OWNER_ABSENT_SEC` seconds:
    - Mark bag as "unattended"
    - Generate `BAG_UNATTENDED` alert
- If owner returns (distance <= `OWNER_MAX_DIST`):
  - Remove bag from unattended set
  - Generate `OWNER_RETURNED` alert

**Configuration:**
- `owner_max_dist`: 120 pixels (default)
- `owner_absent_sec`: 20 seconds (default)

### 2. Loitering Detection

**Logic:**
- For each person, check distance to all unattended bags
- If person is within `LOITER_NEAR_RADIUS` of an unattended bag:
  - Start/continue loitering timer
  - If timer >= `LOITER_NEAR_SEC` seconds:
    - Generate `LOITER_NEAR_UNATTENDED` alert
- If person moves away (distance > `LOITER_NEAR_RADIUS`):
  - Reset loitering timer

**Configuration:**
- `loiter_near_radius`: 70 pixels (default)
- `loiter_near_sec`: 20 seconds (default)

### 3. Running Detection

**Logic:**
- Track person position history (last 5 seconds of positions)
- Calculate speed from position changes between frames
- Speed = distance moved per frame × FPS
- If speed > `RUNNING_SPEED`:
  - Generate `RUNNING` alert

**Configuration:**
- `running_speed`: 260 pixels/second (default)

## Implementation Details

### State Management

The behavior detector maintains the following state:

1. **`bag_owner_lastseen`**: Dictionary mapping bag_id -> last time owner was nearby
2. **`bag_center`**: Dictionary mapping bag_id -> (center_x, center_y)
3. **`unattended_bags`**: Set of bag IDs currently marked as unattended
4. **`person_pos_hist`**: Dictionary mapping person_id -> deque of recent positions (for speed calculation)
5. **`near_unattend_start`**: Nested dictionary mapping (person_id, bag_id) -> start time of loitering

### Alert Types

1. **`BAG_UNATTENDED`**: Bag has been unattended for the threshold time
2. **`OWNER_RETURNED`**: Owner returned to an unattended bag
3. **`LOITER_NEAR_UNATTENDED`**: Person loitering near unattended bag
4. **`RUNNING`**: Person moving faster than threshold speed

### Integration with Tracker

The behavior detector works with the BoTSORT tracker to:
- Get consistent object IDs across frames
- Track object positions over time
- Calculate speeds and distances

## Configuration

All thresholds can be configured in `config.yaml`:

```yaml
behavior:
  owner_max_dist: 120      # pixels
  owner_absent_sec: 20     # seconds
  loiter_near_radius: 70   # pixels
  loiter_near_sec: 20      # seconds
  running_speed: 260       # pixels/second
```

## Notes

- The implementation matches the original notebook logic exactly
- All distance calculations use Euclidean distance (hypot)
- Time-based thresholds are calculated from video FPS
- Alerts are generated once per event (duplicate prevention built-in)
- State is maintained across frames for continuous tracking

## Testing

To test the behavior detection:
1. Process a video with bags and people
2. Check generated alerts in JSON/CSV output
3. Verify annotated video shows correct bounding boxes and labels

