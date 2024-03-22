from app.entities.agent_data import AgentData
from app.entities.processed_agent_data import ProcessedAgentData

# Road states
class RoadStates:
    DeepPits = 'deep pits (poor)'
    SmallPits = 'small pits (fair)'
    GoodRoad = 'good road (good)'
    SmallBumps = 'small bumps (fair)'
    LargeBumps = 'large bumps (poor)'

def process_agent_data(
    agent_data: AgentData,
) -> ProcessedAgentData:
    """
    Process agent data and classify the state of the road surface.
    Parameters:
        agent_data (AgentData): Agent data that containing accelerometer, GPS, and timestamp.
    Returns:
        processed_data_batch (ProcessedAgentData): Processed data containing the classified state of the road surface and agent data.
    """
    # Implement it
    if agent_data.accelerometer.z < -2000:
        road_state = RoadStates.DeepPits
    elif agent_data.accelerometer.z < -1000:
        road_state = RoadStates.SmallPits
    elif agent_data.accelerometer.z < 1000:
        road_state = RoadStates.GoodRoad
    elif agent_data.accelerometer.z < 2000:
        road_state = RoadStates.SmallBumps
    else:
        road_state = RoadStates.LargeBumps

    processed_data = ProcessedAgentData(
        agent_data=agent_data,
        road_state=road_state
    )
    return processed_data
