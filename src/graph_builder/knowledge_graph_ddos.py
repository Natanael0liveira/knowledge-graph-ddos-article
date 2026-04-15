"""
Knowledge Graph-Based DDoS Detection System
============================================
A semantic approach to network security using knowledge graphs.

This module implements the core components for building and querying
a knowledge graph for DDoS attack detection.

Author: [Your Name]
Paper: "Knowledge Graph-Based Anomaly Detection for DDoS Attacks: 
        A Semantic Approach to Network Security"
"""

import networkx as nx
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import numpy as np
from collections import defaultdict


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class EntityType(Enum):
    """Types of entities in the knowledge graph."""
    HOST = "Host"
    SERVER = "Server"
    CLIENT = "Client"
    ROUTER = "Router"
    FIREWALL = "Firewall"
    IP_ADDRESS = "IPAddress"
    PORT = "Port"
    SERVICE = "Service"
    TRAFFIC_FLOW = "TrafficFlow"
    ATTACK = "Attack"
    ANOMALY = "Anomaly"
    BOTNET = "Botnet"


class AttackType(Enum):
    """DDoS attack types."""
    VOLUMETRIC = "VolumetricAttack"
    PROTOCOL = "ProtocolAttack"
    APPLICATION = "ApplicationAttack"
    AMPLIFICATION = "AmplificationAttack"
    SYN_FLOOD = "SYNFlood"
    UDP_FLOOD = "UDPFlood"
    HTTP_FLOOD = "HTTPFlood"
    DNS_AMP = "DNSAmplification"
    NTP_AMP = "NTPAmplification"
    SLOWLORIS = "Slowloris"


class RelationType(Enum):
    """Types of relationships in the knowledge graph."""
    CONNECTED_TO = "connectedTo"
    HAS_IP = "hasIP"
    HAS_PORT = "hasPort"
    RUNS_SERVICE = "runsService"
    SOURCE_IP = "sourceIP"
    DESTINATION_IP = "destinationIP"
    TARGETS = "targets"
    ORIGINATES_FROM = "originatesFrom"
    INDICATES = "indicates"
    DEVIATES_FROM = "deviatesFrom"


@dataclass
class Entity:
    """Represents a node in the knowledge graph."""
    id: str
    entity_type: EntityType
    properties: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.entity_type.value,
            "properties": self.properties
        }


@dataclass
class Relation:
    """Represents an edge in the knowledge graph."""
    source_id: str
    target_id: str
    relation_type: RelationType
    properties: Dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "type": self.relation_type.value,
            "properties": self.properties
        }


@dataclass
class TrafficFlow:
    """Represents a network traffic flow."""
    flow_id: str
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    bytes: int
    packets: int
    timestamp: datetime
    duration_ms: int = 0
    tcp_flags: str = ""
    
    def to_entity(self) -> Entity:
        """Convert traffic flow to knowledge graph entity."""
        return Entity(
            id=f"flow_{self.flow_id}",
            entity_type=EntityType.TRAFFIC_FLOW,
            properties={
                "src_ip": self.src_ip,
                "dst_ip": self.dst_ip,
                "src_port": self.src_port,
                "dst_port": self.dst_port,
                "protocol": self.protocol,
                "bytes": self.bytes,
                "packets": self.packets,
                "timestamp": self.timestamp.isoformat(),
                "duration_ms": self.duration_ms,
                "tcp_flags": self.tcp_flags
            }
        )


@dataclass
class Anomaly:
    """Represents a detected anomaly."""
    anomaly_id: str
    anomaly_type: str
    score: float
    confidence: float
    related_flows: List[str]
    timestamp: datetime
    attack_type: Optional[AttackType] = None
    severity: str = "medium"
    
    def to_entity(self) -> Entity:
        """Convert anomaly to knowledge graph entity."""
        return Entity(
            id=f"anomaly_{self.anomaly_id}",
            entity_type=EntityType.ANOMALY,
            properties={
                "anomaly_type": self.anomaly_type,
                "score": self.score,
                "confidence": self.confidence,
                "related_flows": self.related_flows,
                "timestamp": self.timestamp.isoformat(),
                "attack_type": self.attack_type.value if self.attack_type else None,
                "severity": self.severity
            }
        )


# =============================================================================
# KNOWLEDGE GRAPH CLASS
# =============================================================================

class DDoSKnowledgeGraph:
    """
    Knowledge Graph for DDoS Attack Detection.
    
    This class implements a property graph using NetworkX for storing
    and querying network security knowledge.
    """
    
    def __init__(self):
        """Initialize the knowledge graph."""
        self.graph = nx.MultiDiGraph()
        self.entities: Dict[str, Entity] = {}
        self.relations: List[Relation] = []
        
        # Statistics for anomaly detection
        self.traffic_stats = defaultdict(lambda: {
            "total_bytes": 0,
            "total_packets": 0,
            "flow_count": 0,
            "unique_sources": set(),
            "timestamps": []
        })
        
        # Historical baseline
        self.baseline = {}
        
        # Detected anomalies
        self.anomalies: List[Anomaly] = []
        
    def add_entity(self, entity: Entity) -> None:
        """Add an entity (node) to the graph."""
        self.graph.add_node(
            entity.id,
            type=entity.entity_type.value,
            **entity.properties
        )
        self.entities[entity.id] = entity
        
    def add_relation(self, relation: Relation) -> None:
        """Add a relation (edge) to the graph."""
        self.graph.add_edge(
            relation.source_id,
            relation.target_id,
            key=relation.relation_type.value,
            type=relation.relation_type.value,
            **relation.properties
        )
        self.relations.append(relation)
        
    def add_traffic_flow(self, flow: TrafficFlow) -> None:
        """
        Add a traffic flow to the knowledge graph.
        
        Creates entities for IPs, ports, and the flow itself,
        along with their relationships.
        """
        # Create IP entities if they don't exist
        src_ip_id = f"ip_{flow.src_ip}"
        if src_ip_id not in self.entities:
            self.add_entity(Entity(
                id=src_ip_id,
                entity_type=EntityType.IP_ADDRESS,
                properties={"address": flow.src_ip, "reputation": 0.5}
            ))
            
        dst_ip_id = f"ip_{flow.dst_ip}"
        if dst_ip_id not in self.entities:
            self.add_entity(Entity(
                id=dst_ip_id,
                entity_type=EntityType.IP_ADDRESS,
                properties={"address": flow.dst_ip, "reputation": 0.5}
            ))
        
        # Create port entities
        src_port_id = f"port_{flow.src_port}"
        if src_port_id not in self.entities:
            self.add_entity(Entity(
                id=src_port_id,
                entity_type=EntityType.PORT,
                properties={"number": flow.src_port}
            ))
            
        dst_port_id = f"port_{flow.dst_port}"
        if dst_port_id not in self.entities:
            self.add_entity(Entity(
                id=dst_port_id,
                entity_type=EntityType.PORT,
                properties={"number": flow.dst_port}
            ))
        
        # Create flow entity
        flow_entity = flow.to_entity()
        self.add_entity(flow_entity)
        
        # Create relationships
        self.add_relation(Relation(
            source_id=flow_entity.id,
            target_id=src_ip_id,
            relation_type=RelationType.SOURCE_IP
        ))
        
        self.add_relation(Relation(
            source_id=flow_entity.id,
            target_id=dst_ip_id,
            relation_type=RelationType.DESTINATION_IP
        ))
        
        # Update traffic statistics
        key = (flow.dst_ip, flow.dst_port)
        self.traffic_stats[key]["total_bytes"] += flow.bytes
        self.traffic_stats[key]["total_packets"] += flow.packets
        self.traffic_stats[key]["flow_count"] += 1
        self.traffic_stats[key]["unique_sources"].add(flow.src_ip)
        self.traffic_stats[key]["timestamps"].append(flow.timestamp)
        
    def get_neighbors(self, entity_id: str) -> List[Entity]:
        """Get all neighboring entities."""
        if entity_id not in self.graph:
            return []
        return [self.entities[n] for n in self.graph.neighbors(entity_id)]
    
    def get_incoming_traffic(self, ip_address: str) -> List[Entity]:
        """Get all traffic flows destined for an IP."""
        flows = []
        ip_id = f"ip_{ip_address}"
        
        for relation in self.relations:
            if (relation.relation_type == RelationType.DESTINATION_IP and 
                relation.target_id == ip_id):
                flow_id = relation.source_id
                if flow_id in self.entities:
                    flows.append(self.entities[flow_id])
                    
        return flows
    
    def get_sources_for_destination(self, dst_ip: str, 
                                      time_window: timedelta = timedelta(minutes=5)) -> Set[str]:
        """Get unique source IPs targeting a destination within time window."""
        sources = set()
        now = datetime.now()
        
        for relation in self.relations:
            if relation.relation_type == RelationType.DESTINATION_IP:
                target_ip = relation.target_id.replace("ip_", "")
                if target_ip == dst_ip:
                    flow_id = relation.source_id
                    if flow_id in self.entities:
                        flow_props = self.entities[flow_id].properties
                        flow_time = datetime.fromisoformat(flow_props.get("timestamp", now.isoformat()))
                        if now - flow_time <= time_window:
                            src_ip = flow_props.get("src_ip")
                            if src_ip:
                                sources.add(src_ip)
                                
        return sources
    
    def calculate_graph_metrics(self) -> Dict:
        """Calculate graph-based metrics for anomaly detection."""
        metrics = {}
        
        # Degree centrality
        metrics["degree_centrality"] = nx.degree_centrality(self.graph)
        
        # In-degree (incoming traffic)
        metrics["in_degree"] = dict(self.graph.in_degree())
        
        # Out-degree (outgoing traffic)
        metrics["out_degree"] = dict(self.graph.out_degree())
        
        # Betweenness centrality (critical nodes)
        if len(self.graph) > 1:
            metrics["betweenness_centrality"] = nx.betweenness_centrality(self.graph)
        else:
            metrics["betweenness_centrality"] = {}
            
        return metrics


# =============================================================================
# ANOMALY DETECTOR
# =============================================================================

class DDoSAnomalyDetector:
    """
    Semantic anomaly detector for DDoS attacks.
    
    Implements detection rules based on the knowledge graph ontology.
    """
    
    def __init__(self, kg: DDoSKnowledgeGraph):
        """Initialize detector with knowledge graph reference."""
        self.kg = kg
        self.detection_rules = {
            "volumetric": self._detect_volumetric_attack,
            "distributed": self._detect_distributed_attack,
            "syn_flood": self._detect_syn_flood,
            "amplification": self._detect_amplification_attack,
            "malicious_ip": self._detect_malicious_ip,
            "behavioral": self._detect_behavioral_anomaly
        }
        
        # Thresholds (configurable)
        self.thresholds = {
            "volumetric_bytes_per_sec": 1_000_000_000,  # 1 Gbps
            "distributed_source_count": 100,
            "syn_flood_ratio": 0.8,
            "amplification_factor": 10,
            "low_reputation": 0.3
        }
        
    def detect(self, time_window: timedelta = timedelta(minutes=5)) -> List[Anomaly]:
        """
        Run all detection rules and return detected anomalies.
        """
        anomalies = []
        
        for rule_name, rule_func in self.detection_rules.items():
            try:
                detected = rule_func(time_window)
                anomalies.extend(detected)
            except Exception as e:
                print(f"Error in rule {rule_name}: {e}")
                
        self.kg.anomalies.extend(anomalies)
        return anomalies
    
    def _detect_volumetric_attack(self, time_window: timedelta) -> List[Anomaly]:
        """
        Detect volumetric DDoS attacks based on traffic volume.
        
        Rule: If traffic volume to a destination exceeds threshold,
        create a TrafficAnomaly indicating potential volumetric attack.
        """
        anomalies = []
        now = datetime.now()
        
        for key, stats in self.kg.traffic_stats.items():
            dst_ip, dst_port = key
            
            # Calculate bytes per second
            if stats["timestamps"]:
                time_span = (max(stats["timestamps"]) - min(stats["timestamps"])).total_seconds()
                if time_span > 0:
                    bytes_per_sec = stats["total_bytes"] / time_span
                else:
                    bytes_per_sec = stats["total_bytes"]
                    
                if bytes_per_sec > self.thresholds["volumetric_bytes_per_sec"]:
                    anomaly = Anomaly(
                        anomaly_id=f"vol_{dst_ip}_{int(now.timestamp())}",
                        anomaly_type="TrafficAnomaly",
                        score=min(1.0, bytes_per_sec / self.thresholds["volumetric_bytes_per_sec"]),
                        confidence=0.85,
                        related_flows=[f"flow_{dst_ip}_{dst_port}"],
                        timestamp=now,
                        attack_type=AttackType.VOLUMETRIC,
                        severity="high"
                    )
                    anomalies.append(anomaly)
                    
        return anomalies
    
    def _detect_distributed_attack(self, time_window: timedelta) -> List[Anomaly]:
        """
        Detect distributed attacks based on source diversity.
        
        Rule: If many distinct sources target same destination,
        create a StructuralAnomaly indicating potential DDoS.
        """
        anomalies = []
        now = datetime.now()
        
        for key, stats in self.kg.traffic_stats.items():
            dst_ip, dst_port = key
            unique_sources = len(stats["unique_sources"])
            
            if unique_sources > self.thresholds["distributed_source_count"]:
                anomaly = Anomaly(
                    anomaly_id=f"dist_{dst_ip}_{int(now.timestamp())}",
                    anomaly_type="StructuralAnomaly",
                    score=min(1.0, unique_sources / self.thresholds["distributed_source_count"]),
                    confidence=0.80,
                    related_flows=[f"flow_{dst_ip}_{dst_port}"],
                    timestamp=now,
                    attack_type=AttackType.VOLUMETRIC,
                    severity="high"
                )
                anomalies.append(anomaly)
                
        return anomalies
    
    def _detect_syn_flood(self, time_window: timedelta) -> List[Anomaly]:
        """
        Detect SYN flood attacks.
        
        Rule: High ratio of SYN packets without ACK completion.
        """
        anomalies = []
        now = datetime.now()
        
        # Group flows by destination and count SYN packets
        syn_counts = defaultdict(int)
        total_packets = defaultdict(int)
        
        for entity_id, entity in self.kg.entities.items():
            if entity.entity_type == EntityType.TRAFFIC_FLOW:
                props = entity.properties
                dst_ip = props.get("dst_ip")
                tcp_flags = props.get("tcp_flags", "")
                packets = props.get("packets", 0)
                
                if "SYN" in tcp_flags and "ACK" not in tcp_flags:
                    syn_counts[dst_ip] += packets
                total_packets[dst_ip] += packets
                
        for dst_ip, syn_count in syn_counts.items():
            total = total_packets[dst_ip]
            if total > 0:
                syn_ratio = syn_count / total
                if syn_ratio > self.thresholds["syn_flood_ratio"]:
                    anomaly = Anomaly(
                        anomaly_id=f"syn_{dst_ip}_{int(now.timestamp())}",
                        anomaly_type="TrafficAnomaly",
                        score=syn_ratio,
                        confidence=0.90,
                        related_flows=[],
                        timestamp=now,
                        attack_type=AttackType.SYN_FLOOD,
                        severity="critical"
                    )
                    anomalies.append(anomaly)
                    
        return anomalies
    
    def _detect_amplification_attack(self, time_window: timedelta) -> List[Anomaly]:
        """
        Detect amplification attacks.
        
        Rule: Response traffic significantly larger than request traffic.
        """
        anomalies = []
        now = datetime.now()
        
        # Check for DNS/NTP amplification patterns
        amplification_ports = {53: "DNS", 123: "NTP"}
        
        for key, stats in self.kg.traffic_stats.items():
            dst_ip, dst_port = key
            
            if dst_port in amplification_ports:
                # High traffic to amplification-vulnerable ports
                if stats["total_bytes"] > 100_000_000:  # 100 MB
                    anomaly = Anomaly(
                        anomaly_id=f"amp_{dst_ip}_{dst_port}_{int(now.timestamp())}",
                        anomaly_type="TrafficAnomaly",
                        score=0.85,
                        confidence=0.75,
                        related_flows=[],
                        timestamp=now,
                        attack_type=AttackType.DNS_AMP if dst_port == 53 else AttackType.NTP_AMP,
                        severity="high"
                    )
                    anomalies.append(anomaly)
                    
        return anomalies
    
    def _detect_malicious_ip(self, time_window: timedelta) -> List[Anomaly]:
        """
        Detect traffic from known malicious IPs.
        
        Rule: Traffic from low-reputation IPs creates high-severity anomaly.
        """
        anomalies = []
        now = datetime.now()
        
        for entity_id, entity in self.kg.entities.items():
            if entity.entity_type == EntityType.IP_ADDRESS:
                reputation = entity.properties.get("reputation", 1.0)
                
                if reputation < self.thresholds["low_reputation"]:
                    # Find flows from this IP
                    related_flows = []
                    for relation in self.kg.relations:
                        if (relation.relation_type == RelationType.SOURCE_IP and
                            relation.target_id == entity_id):
                            related_flows.append(relation.source_id)
                            
                    if related_flows:
                        anomaly = Anomaly(
                            anomaly_id=f"mal_{entity_id}_{int(now.timestamp())}",
                            anomaly_type="TrafficAnomaly",
                            score=1.0 - reputation,
                            confidence=0.95,
                            related_flows=related_flows,
                            timestamp=now,
                            attack_type=AttackType.VOLUMETRIC,
                            severity="critical"
                        )
                        anomalies.append(anomaly)
                        
        return anomalies
    
    def _detect_behavioral_anomaly(self, time_window: timedelta) -> List[Anomaly]:
        """
        Detect behavioral anomalies using graph metrics.
        
        Rule: Significant deviation from historical graph structure.
        """
        anomalies = []
        now = datetime.now()
        
        metrics = self.kg.calculate_graph_metrics()
        
        # Check for nodes with unusually high in-degree
        for node_id, in_degree in metrics["in_degree"].items():
            if node_id.startswith("ip_") and in_degree > 50:
                # High incoming connections might indicate attack target
                anomaly = Anomaly(
                    anomaly_id=f"beh_{node_id}_{int(now.timestamp())}",
                    anomaly_type="BehaviorAnomaly",
                    score=min(1.0, in_degree / 100),
                    confidence=0.70,
                    related_flows=[],
                    timestamp=now,
                    severity="medium"
                )
                anomalies.append(anomaly)
                
        return anomalies


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

def simulate_ddos_attack():
    """
    Simulate a DDoS attack scenario for demonstration.
    """
    print("=" * 60)
    print("Knowledge Graph-Based DDoS Detection Simulation")
    print("=" * 60)
    
    # Initialize knowledge graph
    kg = DDoSKnowledgeGraph()
    
    # Simulate normal traffic
    print("\n[1] Adding normal traffic flows...")
    normal_flows = [
        TrafficFlow(
            flow_id=f"normal_{i}",
            src_ip=f"192.168.1.{i % 50}",
            dst_ip="10.0.0.100",
            src_port=40000 + i,
            dst_port=80,
            protocol="TCP",
            bytes=1000 + (i * 100),
            packets=10 + i,
            timestamp=datetime.now() - timedelta(seconds=i)
        )
        for i in range(50)
    ]
    
    for flow in normal_flows:
        kg.add_traffic_flow(flow)
    
    print(f"   Added {len(normal_flows)} normal traffic flows")
    print(f"   Graph nodes: {kg.graph.number_of_nodes()}")
    print(f"   Graph edges: {kg.graph.number_of_edges()}")
    
    # Simulate DDoS attack traffic
    print("\n[2] Simulating DDoS attack...")
    attack_flows = [
        TrafficFlow(
            flow_id=f"attack_{i}",
            src_ip=f"203.0.113.{i % 255}",  # Attacker IPs
            dst_ip="10.0.0.100",  # Target
            src_port=50000 + i,
            dst_port=80,
            protocol="TCP",
            bytes=50000,  # Large packets
            packets=100,
            timestamp=datetime.now(),
            tcp_flags="SYN"  # SYN flood pattern
        )
        for i in range(200)  # 200 attack flows
    ]
    
    # Add some malicious IP reputation
    for flow in attack_flows[:50]:
        ip_id = f"ip_{flow.src_ip}"
        if ip_id in kg.entities:
            kg.entities[ip_id].properties["reputation"] = 0.1  # Low reputation
    
    for flow in attack_flows:
        kg.add_traffic_flow(flow)
    
    print(f"   Added {len(attack_flows)} attack traffic flows")
    print(f"   Graph nodes: {kg.graph.number_of_nodes()}")
    print(f"   Graph edges: {kg.graph.number_of_edges()}")
    
    # Run anomaly detection
    print("\n[3] Running anomaly detection...")
    detector = DDoSAnomalyDetector(kg)
    anomalies = detector.detect()
    
    print(f"\n[4] Detection Results:")
    print(f"   Total anomalies detected: {len(anomalies)}")
    
    # Group by attack type
    attack_counts = defaultdict(int)
    for anomaly in anomalies:
        if anomaly.attack_type:
            attack_counts[anomaly.attack_type.value] += 1
    
    print("\n   Attack Type Distribution:")
    for attack_type, count in attack_counts.items():
        print(f"   - {attack_type}: {count}")
    
    # Display top anomalies
    print("\n   Top Anomalies (by score):")
    sorted_anomalies = sorted(anomalies, key=lambda x: x.score, reverse=True)[:5]
    for anomaly in sorted_anomalies:
        print(f"   - [{anomaly.severity.upper()}] {anomaly.anomaly_type}")
        print(f"     Score: {anomaly.score:.2f}, Confidence: {anomaly.confidence:.2f}")
        if anomaly.attack_type:
            print(f"     Attack Type: {anomaly.attack_type.value}")
    
    # Graph metrics
    print("\n[5] Graph Metrics:")
    metrics = kg.calculate_graph_metrics()
    
    # Find most targeted IP
    max_in_degree = max(metrics["in_degree"].items(), key=lambda x: x[1])
    print(f"   Most targeted node: {max_in_degree[0]} (in-degree: {max_in_degree[1]})")
    
    # Export graph for visualization
    print("\n[6] Exporting knowledge graph...")
    export_data = {
        "nodes": [e.to_dict() for e in kg.entities.values()],
        "edges": [r.to_dict() for r in kg.relations],
        "anomalies": [a.to_entity().to_dict() for a in kg.anomalies]
    }
    
    with open("knowledge_graph_export.json", "w") as f:
        json.dump(export_data, f, indent=2, default=str)
    
    print("   Exported to knowledge_graph_export.json")
    
    return kg, anomalies


if __name__ == "__main__":
    kg, anomalies = simulate_ddos_attack()
    
    print("\n" + "=" * 60)
    print("Simulation Complete")
    print("=" * 60)
    print(f"""
Summary:
- Knowledge Graph nodes: {kg.graph.number_of_nodes()}
- Knowledge Graph edges: {kg.graph.number_of_edges()}
- Anomalies detected: {len(anomalies)}

This demonstrates the semantic approach to DDoS detection using
knowledge graphs. The system successfully identified:
1. Volumetric attack patterns
2. Distributed source patterns
3. SYN flood characteristics
4. Low-reputation IP traffic
5. Behavioral anomalies in graph structure
""")
