"""
Knowledge Graph-Based Layer 7 DDoS Detection System
====================================================
A semantic approach to web application security using knowledge graphs.

This module implements the core components for building and querying
a knowledge graph for Layer 7 DDoS attack detection in web applications.

Author: [Your Name]
Paper: "Knowledge Graph-Based Detection and Explanation of Layer 7 DDoS Attacks in Web Applications"
"""

import networkx as nx
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import math
import numpy as np
from collections import defaultdict, Counter


# =============================================================================
# ENUMS AND DATA CLASSES - Layer 7 Specific
# =============================================================================

class EntityType(Enum):
    """Types of entities in the Layer 7 knowledge graph."""
    # HTTP Entities
    HTTP_REQUEST = "HTTPRequest"
    ENDPOINT = "Endpoint"
    HTTP_HEADER = "HTTPHeader"
    USER_AGENT = "UserAgent"
    
    # DNS Entities (Layer 7 DNS Attacks)
    DNS_QUERY = "DNSQuery"
    DNS_RESPONSE = "DNSResponse"
    DNS_DOMAIN = "DNSDomain"
    DNS_SUBDOMAIN = "DNSSubdomain"
    DNS_RESOLVER = "DNSResolver"
    DNS_SERVER = "DNSServer"
    DNS_RECORD_TYPE = "DNSRecordType"
    
    # Session Entities
    APPLICATION_SESSION = "ApplicationSession"
    SESSION_TOKEN = "SessionToken"
    COOKIE = "Cookie"
    IDENTITY = "Identity"
    
    # Behavior Entities
    BEHAVIOR = "Behavior"
    USER_BEHAVIOR = "UserBehavior"
    BOT_BEHAVIOR = "BotBehavior"
    NAVIGATION_PATTERN = "NavigationPattern"
    REQUEST_PATTERN = "RequestPattern"
    DNS_QUERY_PATTERN = "DNSQueryPattern"
    
    # Attack Entities
    ATTACK = "Attack"
    DDOS_ATTACK = "DDoSAttack"
    APPLICATION_LAYER_ATTACK = "ApplicationLayerAttack"
    HTTP_FLOOD = "HTTPFlood"
    LOGIN_FLOOD = "LoginFlood"
    SLOW_REQUEST_ATTACK = "SlowRequestAttack"
    API_ATTACK = "APIAttack"
    SCRAPING_ATTACK = "ScrapingAttack"
    
    # DNS Attack Entities
    DNS_ATTACK = "DNSAttack"
    QNAME_RANDOMIZATION = "QNameRandomization"
    NXDOMAIN_FLOOD = "NXDOMAINFlood"
    DNS_WATER_TORTURE = "DNSWaterTorture"
    DNS_AMPLIFICATION = "DNSAmplification"
    DNS_TUNNELING = "DNSTunneling"
    PHANTOM_DOMAIN = "PhantomDomainAttack"
    
    # Mitigation Entities
    MITIGATION = "Mitigation"
    WAF_RULE = "WAFRule"
    RATE_LIMIT_POLICY = "RateLimitPolicy"
    CHALLENGE_RESPONSE = "ChallengeResponse"
    CACHE_LAYER = "CacheLayer"
    DNS_FIREWALL = "DNSFirewall"
    DNS_RATE_LIMIT = "DNSRateLimit"
    RESPONSE_RATE_LIMITING = "ResponseRateLimiting"
    
    # Backend Entities
    BACKEND_RESOURCE = "BackendResource"
    DATABASE = "Database"
    APPLICATION_SERVER = "ApplicationServer"
    
    # Signal Entities
    ANOMALY = "Anomaly"
    ANOMALY_SIGNAL = "AnomalySignal"
    ALERT = "Alert"
    
    # Legacy Support
    IP_ADDRESS = "IPAddress"
    HOST = "Host"
    SERVER = "Server"


class Layer7AttackType(Enum):
    """Layer 7 DDoS attack types."""
    # HTTP/Application Layer Attacks
    HTTP_FLOOD = "HTTPFlood"
    LOGIN_FLOOD = "LoginFlood"
    SLOW_REQUEST = "SlowRequestAttack"
    SLOWLORIS = "Slowloris"
    RUDY = "RUDY"
    API_ABUSE = "APIAttack"
    SCRAPING = "ScrapingAttack"
    CACHE_BYPASS = "CacheBypassAttack"
    BOT_ATTACK = "BotBehavior"
    
    # DNS Layer 7 Attacks
    QNAME_RANDOMIZATION = "QNameRandomization"
    NXDOMAIN_FLOOD = "NXDOMAINFlood"
    DNS_WATER_TORTURE = "DNSWaterTorture"
    DNS_AMPLIFICATION = "DNSAmplification"
    DNS_TUNNELING = "DNSTunneling"
    PHANTOM_DOMAIN = "PhantomDomainAttack"
    RANDOM_SUBDOMAIN = "RandomSubdomainAttack"


class RelationType(Enum):
    """Types of relationships in the Layer 7 knowledge graph."""
    # Endpoint Relations
    TARGETS_ENDPOINT = "targetsEndpoint"
    ABUSES_FUNCTION = "abusesFunction"
    HAS_ENDPOINT = "hasEndpoint"
    REQUIRES_AUTH = "requiresAuthentication"
    DEPENDS_ON_DB = "dependsOnDatabase"
    
    # Session Relations
    HAS_SESSION = "hasSession"
    HAS_TOKEN = "hasToken"
    HAS_COOKIE = "hasCookie"
    BELONGS_TO_IDENTITY = "belongsToIdentity"
    
    # Behavior Relations
    EXHIBITS_BEHAVIOR = "exhibitsBehavior"
    RESEMBLES_LEGITIMATE = "resemblesLegitimateTraffic"
    DEVIATES_FROM = "deviatesFrom"
    
    # Impact Relations
    INCREASES_LATENCY = "increasesLatency"
    CONSUMES_RESOURCE = "consumesBackendResource"
    EXHAUSTS_RESOURCE = "exhaustsResource"
    
    # Mitigation Relations
    MITIGATED_BY = "mitigatedBy"
    PROTECTED_BY = "protectedBy"
    CACHED_BY = "cachedBy"
    RATE_LIMITED_BY = "rateLimitedBy"
    
    # Detection Relations
    TRIGGERED_BY = "triggeredBy"
    EVIDENCED_BY = "evidencedBy"
    INDICATES = "indicates"
    DETECTED_BY = "detectedBy"
    GENERATES = "generates"
    
    # Legacy Relations
    HAS_IP = "hasIP"
    SOURCE_IP = "sourceIP"
    DESTINATION_IP = "destinationIP"
    TARGETS = "targets"
    ORIGINATES_FROM = "originatesFrom"


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
class HTTPRequest:
    """Represents an HTTP request with Layer 7 specific attributes."""
    request_id: str
    method: str
    path: str
    endpoint: str
    src_ip: str
    user_agent: str
    referer: str = ""
    session_id: str = ""
    token: str = ""
    response_code: int = 0
    response_time_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    headers: Dict = field(default_factory=dict)
    body_size: int = 0
    
    def to_entity(self) -> Entity:
        """Convert HTTP request to knowledge graph entity."""
        return Entity(
            id=f"req_{self.request_id}",
            entity_type=EntityType.HTTP_REQUEST,
            properties={
                "method": self.method,
                "path": self.path,
                "endpoint": self.endpoint,
                "src_ip": self.src_ip,
                "user_agent": self.user_agent,
                "referer": self.referer,
                "session_id": self.session_id,
                "token": self.token,
                "response_code": self.response_code,
                "response_time_ms": self.response_time_ms,
                "timestamp": self.timestamp.isoformat(),
                "headers": self.headers,
                "body_size": self.body_size
            }
        )


@dataclass
class ApplicationSession:
    """Represents a web application session."""
    session_id: str
    identity: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    request_count: int = 0
    unique_endpoints: Set[str] = field(default_factory=set)
    login_attempts: int = 0
    failed_logins: int = 0
    session_value: float = 0.0
    is_authenticated: bool = False
    
    def to_entity(self) -> Entity:
        """Convert session to knowledge graph entity."""
        return Entity(
            id=f"session_{self.session_id}",
            entity_type=EntityType.APPLICATION_SESSION,
            properties={
                "identity": self.identity,
                "ip_address": self.ip_address,
                "user_agent": self.user_agent,
                "created_at": self.created_at.isoformat(),
                "last_activity": self.last_activity.isoformat(),
                "request_count": self.request_count,
                "unique_endpoints_count": len(self.unique_endpoints),
                "login_attempts": self.login_attempts,
                "failed_logins": self.failed_logins,
                "session_value": self.session_value,
                "is_authenticated": self.is_authenticated,
                "session_age": (self.last_activity - self.created_at).total_seconds()
            }
        )


@dataclass
class Endpoint:
    """Represents a web application endpoint."""
    path: str
    computational_cost: float  # 0-1 scale
    is_cacheable: bool
    requires_auth: bool
    depends_on_db: bool
    criticality: str = "medium"  # low, medium, high, critical
    average_response_time_ms: int = 0
    
    def to_entity(self) -> Entity:
        """Convert endpoint to knowledge graph entity."""
        return Entity(
            id=f"endpoint_{self.path.replace('/', '_')}",
            entity_type=EntityType.ENDPOINT,
            properties={
                "path": self.path,
                "computational_cost": self.computational_cost,
                "is_cacheable": self.is_cacheable,
                "requires_auth": self.requires_auth,
                "depends_on_db": self.depends_on_db,
                "criticality": self.criticality,
                "average_response_time_ms": self.average_response_time_ms
            }
        )


@dataclass
class BehaviorProfile:
    """Represents a behavior profile for a session or identity."""
    profile_id: str
    session_id: str
    header_variability: float = 1.0  # 0-1
    fingerprint_variability: float = 1.0  # 0-1
    navigation_diversity: float = 1.0  # 0-1
    request_interval_avg_ms: float = 1000.0
    request_interval_std: float = 500.0
    is_bot_like: bool = False
    pattern_type: str = "normal"  # normal, suspicious, malicious
    
    def to_entity(self) -> Entity:
        """Convert behavior profile to knowledge graph entity."""
        return Entity(
            id=f"behavior_{self.profile_id}",
            entity_type=EntityType.BEHAVIOR,
            properties={
                "session_id": self.session_id,
                "header_variability": self.header_variability,
                "fingerprint_variability": self.fingerprint_variability,
                "navigation_diversity": self.navigation_diversity,
                "request_interval_avg_ms": self.request_interval_avg_ms,
                "request_interval_std": self.request_interval_std,
                "is_bot_like": self.is_bot_like,
                "pattern_type": self.pattern_type
            }
        )


@dataclass
class Anomaly:
    """Represents a detected Layer 7 anomaly."""
    anomaly_id: str
    anomaly_type: str
    score: float
    confidence: float
    related_requests: List[str]
    related_sessions: List[str]
    timestamp: datetime
    attack_type: Optional[Layer7AttackType] = None
    severity: str = "medium"
    explanation: str = ""
    target_endpoint: str = ""
    evidence: List[str] = field(default_factory=list)
    
    def to_entity(self) -> Entity:
        """Convert anomaly to knowledge graph entity."""
        return Entity(
            id=f"anomaly_{self.anomaly_id}",
            entity_type=EntityType.ANOMALY,
            properties={
                "anomaly_type": self.anomaly_type,
                "score": self.score,
                "confidence": self.confidence,
                "related_requests": self.related_requests,
                "related_sessions": self.related_sessions,
                "timestamp": self.timestamp.isoformat(),
                "attack_type": self.attack_type.value if self.attack_type else None,
                "severity": self.severity,
                "explanation": self.explanation,
                "target_endpoint": self.target_endpoint,
                "evidence": self.evidence
            }
        )


# =============================================================================
# DNS LAYER 7 DATA CLASSES
# =============================================================================

@dataclass
class DNSQuery:
    """Represents a DNS query with Layer 7 specific attributes."""
    query_id: str
    qname: str  # Query name (domain being queried)
    qtype: str  # Query type (A, AAAA, MX, TXT, ANY, etc.)
    src_ip: str
    dst_ip: str  # DNS resolver/server
    response_code: str = "NOERROR"  # NOERROR, NXDOMAIN, SERVFAIL, etc.
    response_time_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    answer_count: int = 0
    is_response_cached: bool = False
    query_size: int = 0
    response_size: int = 0
    edns_enabled: bool = False
    dnssec_ok: bool = False
    
    def to_entity(self) -> Entity:
        """Convert DNS query to knowledge graph entity."""
        return Entity(
            id=f"dns_query_{self.query_id}",
            entity_type=EntityType.DNS_QUERY,
            properties={
                "qname": self.qname,
                "qtype": self.qtype,
                "src_ip": self.src_ip,
                "dst_ip": self.dst_ip,
                "response_code": self.response_code,
                "response_time_ms": self.response_time_ms,
                "timestamp": self.timestamp.isoformat(),
                "answer_count": self.answer_count,
                "is_response_cached": self.is_response_cached,
                "query_size": self.query_size,
                "response_size": self.response_size,
                "edns_enabled": self.edns_enabled,
                "dnssec_ok": self.dnssec_ok
            }
        )
    
    def get_base_domain(self) -> str:
        """Extract base domain from qname (e.g., example.com from www.example.com)."""
        parts = self.qname.rstrip('.').split('.')
        if len(parts) >= 2:
            return '.'.join(parts[-2:])
        return self.qname
    
    def get_subdomain(self) -> str:
        """Extract subdomain part from qname."""
        parts = self.qname.rstrip('.').split('.')
        if len(parts) > 2:
            return '.'.join(parts[:-2])
        return ""
    
    def is_random_subdomain(self) -> bool:
        """Check if subdomain appears to be randomly generated."""
        subdomain = self.get_subdomain()
        if not subdomain:
            return False
        
        # Check for high entropy (random characters)
        import math
        from collections import Counter
        
        if len(subdomain) < 8:
            return False
        
        # Calculate entropy
        counts = Counter(subdomain.lower())
        probs = [c/len(subdomain) for c in counts.values()]
        entropy = -sum(p * math.log2(p) for p in probs)
        
        # High entropy + long subdomain = likely random
        return entropy > 3.5 and len(subdomain) > 10


@dataclass
class DNSDomain:
    """Represents a DNS domain being monitored."""
    domain: str
    is_authoritative: bool
    is_internal: bool
    expected_query_rate: float = 10.0  # queries per second baseline
    record_types: Set[str] = field(default_factory=set)
    subdomain_count: int = 0
    last_query_timestamp: datetime = field(default_factory=datetime.now)
    
    def to_entity(self) -> Entity:
        """Convert DNS domain to knowledge graph entity."""
        return Entity(
            id=f"dns_domain_{self.domain.replace('.', '_')}",
            entity_type=EntityType.DNS_DOMAIN,
            properties={
                "domain": self.domain,
                "is_authoritative": self.is_authoritative,
                "is_internal": self.is_internal,
                "expected_query_rate": self.expected_query_rate,
                "record_types": list(self.record_types),
                "subdomain_count": self.subdomain_count,
                "last_query_timestamp": self.last_query_timestamp.isoformat()
            }
        )


@dataclass
class DNSQueryPattern:
    """Represents a DNS query pattern for behavior analysis."""
    pattern_id: str
    src_ip: str
    query_count: int = 0
    unique_domains: Set[str] = field(default_factory=set)
    unique_qtypes: Set[str] = field(default_factory=set)
    nxdomain_count: int = 0
    avg_subdomain_length: float = 0.0
    subdomain_entropy_avg: float = 0.0
    random_subdomain_ratio: float = 0.0
    query_interval_avg_ms: float = 0.0
    query_interval_std: float = 0.0
    is_suspicious: bool = False
    pattern_type: str = "normal"  # normal, random_qname, nxdomain_flood, tunneling
    
    def to_entity(self) -> Entity:
        """Convert DNS query pattern to knowledge graph entity."""
        return Entity(
            id=f"dns_pattern_{self.pattern_id}",
            entity_type=EntityType.DNS_QUERY_PATTERN,
            properties={
                "src_ip": self.src_ip,
                "query_count": self.query_count,
                "unique_domains_count": len(self.unique_domains),
                "unique_qtypes": list(self.unique_qtypes),
                "nxdomain_count": self.nxdomain_count,
                "avg_subdomain_length": self.avg_subdomain_length,
                "subdomain_entropy_avg": self.subdomain_entropy_avg,
                "random_subdomain_ratio": self.random_subdomain_ratio,
                "query_interval_avg_ms": self.query_interval_avg_ms,
                "query_interval_std": self.query_interval_std,
                "is_suspicious": self.is_suspicious,
                "pattern_type": self.pattern_type
            }
        )
    timestamp: datetime
    attack_type: Optional[Layer7AttackType] = None
    severity: str = "medium"
    explanation: str = ""
    target_endpoint: str = ""
    evidence: List[str] = field(default_factory=list)
    
    def to_entity(self) -> Entity:
        """Convert anomaly to knowledge graph entity."""
        return Entity(
            id=f"anomaly_{self.anomaly_id}",
            entity_type=EntityType.ANOMALY,
            properties={
                "anomaly_type": self.anomaly_type,
                "score": self.score,
                "confidence": self.confidence,
                "related_requests": self.related_requests,
                "related_sessions": self.related_sessions,
                "timestamp": self.timestamp.isoformat(),
                "attack_type": self.attack_type.value if self.attack_type else None,
                "severity": self.severity,
                "explanation": self.explanation,
                "target_endpoint": self.target_endpoint,
                "evidence": self.evidence
            }
        )


# =============================================================================
# LAYER 7 KNOWLEDGE GRAPH CLASS
# =============================================================================

class Layer7KnowledgeGraph:
    """
    Knowledge Graph for Layer 7 DDoS Attack Detection.
    
    This class implements a property graph using NetworkX for storing
    and querying web application security knowledge with focus on
    Layer 7 attacks, sessions, endpoints, and behavioral patterns.
    """
    
    def __init__(self):
        """Initialize the Layer 7 knowledge graph."""
        self.graph = nx.MultiDiGraph()
        self.entities: Dict[str, Entity] = {}
        self.relations: List[Relation] = []
        
        # Session tracking
        self.sessions: Dict[str, ApplicationSession] = {}
        
        # Endpoint tracking
        self.endpoints: Dict[str, Endpoint] = {}
        
        # Request statistics per endpoint
        self.endpoint_stats = defaultdict(lambda: {
            "request_count": 0,
            "total_response_time": 0,
            "error_count": 0,
            "unique_sessions": set(),
            "timestamps": []
        })
        
        # Session statistics
        self.session_stats = defaultdict(lambda: {
            "request_count": 0,
            "endpoints_visited": set(),
            "timestamps": [],
            "response_times": [],
            "error_count": 0
        })
        
        # Behavior profiles
        self.behavior_profiles: Dict[str, BehaviorProfile] = {}
        
        # Detected anomalies
        self.anomalies: List[Anomaly] = []
        
        # DNS tracking
        self.dns_queries: Dict[str, DNSQuery] = {}
        self.dns_domains: Dict[str, DNSDomain] = {}
        self.dns_patterns: Dict[str, DNSQueryPattern] = {}
        
        # DNS statistics per source IP
        self.dns_stats = defaultdict(lambda: {
            "query_count": 0,
            "unique_domains": set(),
            "nxdomain_count": 0,
            "timestamps": [],
            "subdomains": [],
            "qtypes": set(),
            "random_subdomain_count": 0
        })
        
        # DNS statistics per domain
        self.domain_stats = defaultdict(lambda: {
            "query_count": 0,
            "unique_subdomains": set(),
            "src_ips": set(),
            "timestamps": [],
            "nxdomain_ratio": 0.0
        })
        
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
        
    def register_endpoint(self, endpoint: Endpoint) -> None:
        """Register an endpoint in the knowledge graph."""
        entity = endpoint.to_entity()
        self.add_entity(entity)
        self.endpoints[endpoint.path] = endpoint
    
    def register_dns_domain(self, domain: DNSDomain) -> None:
        """Register a DNS domain in the knowledge graph."""
        entity = domain.to_entity()
        self.add_entity(entity)
        self.dns_domains[domain.domain] = domain
        
    def add_http_request(self, request: HTTPRequest) -> None:
        """
        Add an HTTP request to the knowledge graph.
        
        Creates entities for the request, updates session tracking,
        and establishes relationships with endpoints.
        """
        # Create IP entity if needed
        ip_id = f"ip_{request.src_ip}"
        if ip_id not in self.entities:
            self.add_entity(Entity(
                id=ip_id,
                entity_type=EntityType.IP_ADDRESS,
                properties={"address": request.src_ip, "reputation": 0.5}
            ))
        
        # Create or update endpoint entity
        endpoint_id = f"endpoint_{request.endpoint.replace('/', '_')}"
        if request.endpoint not in self.endpoints:
            # Auto-create endpoint with default values
            endpoint = Endpoint(
                path=request.endpoint,
                computational_cost=0.5,
                is_cacheable=request.method == "GET",
                requires_auth=False,
                depends_on_db=True
            )
            self.register_endpoint(endpoint)
        
        # Create request entity
        request_entity = request.to_entity()
        self.add_entity(request_entity)
        
        # Create relationships
        self.add_relation(Relation(
            source_id=request_entity.id,
            target_id=ip_id,
            relation_type=RelationType.SOURCE_IP
        ))
        
        self.add_relation(Relation(
            source_id=request_entity.id,
            target_id=endpoint_id,
            relation_type=RelationType.HAS_ENDPOINT
        ))
        
        # Update session if present
        if request.session_id:
            self._update_session(request)
            session_id = f"session_{request.session_id}"
            self.add_relation(Relation(
                source_id=request_entity.id,
                target_id=session_id,
                relation_type=RelationType.HAS_SESSION
            ))
        
        # Update endpoint statistics
        stats = self.endpoint_stats[request.endpoint]
        stats["request_count"] += 1
        stats["total_response_time"] += request.response_time_ms
        if request.response_code >= 400:
            stats["error_count"] += 1
        if request.session_id:
            stats["unique_sessions"].add(request.session_id)
        stats["timestamps"].append(request.timestamp)
        
    def _update_session(self, request: HTTPRequest) -> None:
        """Update or create session tracking."""
        session_id = request.session_id
        
        if session_id not in self.sessions:
            session = ApplicationSession(
                session_id=session_id,
                identity=request.token or "anonymous",
                ip_address=request.src_ip,
                user_agent=request.user_agent,
                created_at=request.timestamp,
                last_activity=request.timestamp
            )
            self.sessions[session_id] = session
        else:
            session = self.sessions[session_id]
            session.last_activity = request.timestamp
            session.request_count += 1
            session.unique_endpoints.add(request.endpoint)
            
        # Update session stats
        stats = self.session_stats[session_id]
        stats["request_count"] += 1
        stats["endpoints_visited"].add(request.endpoint)
        stats["timestamps"].append(request.timestamp)
        stats["response_times"].append(request.response_time_ms)
        if request.response_code >= 400:
            stats["error_count"] += 1
            
    def update_behavior_profile(self, profile: BehaviorProfile) -> None:
        """Add or update a behavior profile."""
        entity = profile.to_entity()
        self.add_entity(entity)
        self.behavior_profiles[profile.profile_id] = profile
        
        # Link to session
        session_id = f"session_{profile.session_id}"
        if session_id in self.entities:
            self.add_relation(Relation(
                source_id=session_id,
                target_id=entity.id,
                relation_type=RelationType.EXHIBITS_BEHAVIOR
            ))
    
    def get_requests_for_endpoint(self, endpoint_path: str) -> List[Entity]:
        """Get all requests targeting a specific endpoint."""
        requests = []
        endpoint_id = f"endpoint_{endpoint_path.replace('/', '_')}"
        
        for relation in self.relations:
            if (relation.relation_type == RelationType.HAS_ENDPOINT and
                relation.target_id == endpoint_id):
                request_id = relation.source_id
                if request_id in self.entities:
                    requests.append(self.entities[request_id])
                    
        return requests
    
    def get_session_requests(self, session_id: str) -> List[Entity]:
        """Get all requests from a specific session."""
        requests = []
        full_session_id = f"session_{session_id}"
        
        for relation in self.relations:
            if (relation.relation_type == RelationType.HAS_SESSION and
                relation.target_id == full_session_id):
                request_id = relation.source_id
                if request_id in self.entities:
                    requests.append(self.entities[request_id])
                    
        return requests
    
    def calculate_endpoint_metrics(self) -> Dict:
        """Calculate metrics for each endpoint."""
        metrics = {}
        
        for endpoint_path, stats in self.endpoint_stats.items():
            if stats["request_count"] > 0:
                avg_response_time = stats["total_response_time"] / stats["request_count"]
                error_rate = stats["error_count"] / stats["request_count"]
                
                # Calculate requests per second
                if len(stats["timestamps"]) >= 2:
                    time_span = (max(stats["timestamps"]) - min(stats["timestamps"])).total_seconds()
                    rps = stats["request_count"] / max(time_span, 1)
                else:
                    rps = 0
                
                metrics[endpoint_path] = {
                    "request_count": stats["request_count"],
                    "avg_response_time_ms": avg_response_time,
                    "error_rate": error_rate,
                    "requests_per_second": rps,
                    "unique_sessions": len(stats["unique_sessions"])
                }
                
        return metrics
    
    def calculate_session_metrics(self) -> Dict:
        """Calculate metrics for each session."""
        metrics = {}
        
        for session_id, stats in self.session_stats.items():
            if stats["request_count"] > 0:
                # Calculate request rate
                if len(stats["timestamps"]) >= 2:
                    time_span = (max(stats["timestamps"]) - min(stats["timestamps"])).total_seconds()
                    rps = stats["request_count"] / max(time_span, 1)
                else:
                    rps = 0
                
                # Calculate navigation diversity
                nav_diversity = len(stats["endpoints_visited"]) / max(stats["request_count"], 1)
                
                # Calculate response time stats
                if stats["response_times"]:
                    avg_response_time = np.mean(stats["response_times"])
                    std_response_time = np.std(stats["response_times"])
                else:
                    avg_response_time = 0
                    std_response_time = 0
                
                metrics[session_id] = {
                    "request_count": stats["request_count"],
                    "requests_per_second": rps,
                    "navigation_diversity": nav_diversity,
                    "unique_endpoints": len(stats["endpoints_visited"]),
                    "avg_response_time_ms": avg_response_time,
                    "response_time_std": std_response_time,
                    "error_count": stats["error_count"]
                }
                
        return metrics
    
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
    
    def add_dns_query(self, query: DNSQuery) -> None:
        """
        Add a DNS query to the knowledge graph.
        
        Creates entities for the query, updates DNS tracking,
        and establishes relationships with domains and resolvers.
        """
        # Create IP entity if needed
        src_ip_id = f"ip_{query.src_ip}"
        if src_ip_id not in self.entities:
            self.add_entity(Entity(
                id=src_ip_id,
                entity_type=EntityType.IP_ADDRESS,
                properties={"address": query.src_ip, "reputation": 0.5}
            ))
        
        # Create DNS server entity if needed
        dst_ip_id = f"dns_server_{query.dst_ip}"
        if dst_ip_id not in self.entities:
            self.add_entity(Entity(
                id=dst_ip_id,
                entity_type=EntityType.DNS_SERVER,
                properties={"address": query.dst_ip}
            ))
        
        # Create or update domain entity
        base_domain = query.get_base_domain()
        domain_id = f"dns_domain_{base_domain.replace('.', '_')}"
        if base_domain not in self.dns_domains:
            domain = DNSDomain(
                domain=base_domain,
                is_authoritative=False,
                is_internal=False
            )
            self.dns_domains[base_domain] = domain
            self.add_entity(domain.to_entity())
        
        # Create DNS query entity
        query_entity = query.to_entity()
        self.add_entity(query_entity)
        self.dns_queries[query.query_id] = query
        
        # Create relationships
        self.add_relation(Relation(
            source_id=query_entity.id,
            target_id=src_ip_id,
            relation_type=RelationType.SOURCE_IP
        ))
        
        self.add_relation(Relation(
            source_id=query_entity.id,
            target_id=dst_ip_id,
            relation_type=RelationType.TARGETS
        ))
        
        self.add_relation(Relation(
            source_id=query_entity.id,
            target_id=domain_id,
            relation_type=RelationType.TARGETS_ENDPOINT
        ))
        
        # Update DNS statistics per source IP
        dns_stats = self.dns_stats[query.src_ip]
        dns_stats["query_count"] += 1
        dns_stats["unique_domains"].add(base_domain)
        dns_stats["timestamps"].append(query.timestamp)
        dns_stats["qtypes"].add(query.qtype)
        
        subdomain = query.get_subdomain()
        if subdomain:
            dns_stats["subdomains"].append(subdomain)
            if query.is_random_subdomain():
                dns_stats["random_subdomain_count"] += 1
        
        if query.response_code == "NXDOMAIN":
            dns_stats["nxdomain_count"] += 1
        
        # Update domain statistics
        domain_stats = self.domain_stats[base_domain]
        domain_stats["query_count"] += 1
        domain_stats["src_ips"].add(query.src_ip)
        domain_stats["timestamps"].append(query.timestamp)
        if subdomain:
            domain_stats["unique_subdomains"].add(subdomain)
        
        # Calculate NXDOMAIN ratio for domain
        nxdomain_count = sum(1 for q in self.dns_queries.values() 
                           if q.get_base_domain() == base_domain and q.response_code == "NXDOMAIN")
        if domain_stats["query_count"] > 0:
            domain_stats["nxdomain_ratio"] = nxdomain_count / domain_stats["query_count"]
    
    def calculate_dns_metrics(self) -> Dict:
        """Calculate metrics for DNS traffic analysis."""
        metrics = {}
        
        for src_ip, stats in self.dns_stats.items():
            if stats["query_count"] > 0:
                # Calculate queries per second
                if len(stats["timestamps"]) >= 2:
                    time_span = (max(stats["timestamps"]) - min(stats["timestamps"])).total_seconds()
                    qps = stats["query_count"] / max(time_span, 1)
                else:
                    qps = 0
                
                # Calculate random subdomain ratio
                subdomain_count = len(stats["subdomains"])
                random_ratio = stats["random_subdomain_count"] / max(subdomain_count, 1)
                
                # Calculate NXDOMAIN ratio
                nxdomain_ratio = stats["nxdomain_count"] / stats["query_count"]
                
                # Calculate average subdomain length
                avg_subdomain_len = np.mean([len(s) for s in stats["subdomains"]]) if stats["subdomains"] else 0
                
                # Calculate subdomain entropy average
                entropies = []
                for subdomain in stats["subdomains"]:
                    if len(subdomain) >= 4:
                        counts = Counter(subdomain.lower())
                        probs = [c/len(subdomain) for c in counts.values()]
                        entropy = -sum(p * math.log2(p) for p in probs)
                        entropies.append(entropy)
                avg_entropy = np.mean(entropies) if entropies else 0
                
                metrics[src_ip] = {
                    "query_count": stats["query_count"],
                    "queries_per_second": qps,
                    "unique_domains": len(stats["unique_domains"]),
                    "nxdomain_count": stats["nxdomain_count"],
                    "nxdomain_ratio": nxdomain_ratio,
                    "random_subdomain_count": stats["random_subdomain_count"],
                    "random_subdomain_ratio": random_ratio,
                    "unique_qtypes": len(stats["qtypes"]),
                    "avg_subdomain_length": avg_subdomain_len,
                    "subdomain_entropy_avg": avg_entropy,
                    "unique_subdomains": len(set(stats["subdomains"]))
                }
        
        return metrics
    
    def calculate_domain_metrics(self) -> Dict:
        """Calculate metrics per DNS domain."""
        metrics = {}
        
        for domain, stats in self.domain_stats.items():
            if stats["query_count"] > 0:
                # Calculate queries per second
                if len(stats["timestamps"]) >= 2:
                    time_span = (max(stats["timestamps"]) - min(stats["timestamps"])).total_seconds()
                    qps = stats["query_count"] / max(time_span, 1)
                else:
                    qps = 0
                
                metrics[domain] = {
                    "query_count": stats["query_count"],
                    "queries_per_second": qps,
                    "unique_src_ips": len(stats["src_ips"]),
                    "unique_subdomains": len(stats["unique_subdomains"]),
                    "nxdomain_ratio": stats["nxdomain_ratio"]
                }
        
        return metrics


# =============================================================================
# LAYER 7 ANOMALY DETECTOR
# =============================================================================

class Layer7AnomalyDetector:
    """
    Semantic anomaly detector for Layer 7 DDoS attacks.
    
    Implements detection rules based on application behavior,
    session patterns, and endpoint characteristics.
    """
    
    def __init__(self, kg: Layer7KnowledgeGraph):
        """Initialize detector with knowledge graph reference."""
        self.kg = kg
        self.detection_rules = {
            # Layer 7 specific rules
            "login_flood": self._detect_login_flood,
            "http_flood": self._detect_http_flood,
            "bot_behavior": self._detect_bot_behavior,
            "low_session_value": self._detect_low_session_value,
            "expensive_endpoint_burst": self._detect_expensive_endpoint_burst,
            "latency_increase": self._detect_latency_increase,
            "repetitive_route": self._detect_repetitive_route,
            "slow_request": self._detect_slow_request,
            "scraping": self._detect_scraping,
            "api_abuse": self._detect_api_abuse,
            # DNS Layer 7 specific rules
            "qname_randomization": self._detect_qname_randomization,
            "nxdomain_flood": self._detect_nxdomain_flood,
            "dns_water_torture": self._detect_dns_water_torture,
            "dns_amplification": self._detect_dns_amplification,
            "phantom_domain": self._detect_phantom_domain,
            "dns_tunneling": self._detect_dns_tunneling
        }
        
        # Layer 7 specific thresholds
        self.thresholds = {
            "login_failures_per_session": 10,
            "requests_per_second_per_session": 50,
            "header_variability_threshold": 0.15,
            "fingerprint_variability_threshold": 0.15,
            "navigation_diversity_threshold": 0.2,
            "session_value_threshold": 0.1,
            "expensive_endpoint_rps": 30,
            "latency_multiplier": 3.0,
            "slow_request_ms": 30000,
            "scraping_endpoints": 50,
            "api_error_rate": 0.3,
            # DNS Layer 7 specific thresholds
            "dns_qps_per_ip": 100,  # Queries per second threshold
            "random_subdomain_ratio": 0.7,  # Ratio of random subdomains
            "nxdomain_ratio": 0.6,  # NXDOMAIN ratio threshold
            "unique_subdomains_per_domain": 500,  # Unique subdomains threshold
            "dns_entropy_threshold": 3.5,  # Entropy threshold for random names
            "dns_query_size_bytes": 100,  # Large query size threshold
            "dns_response_size_bytes": 1000,  # Large response (amplification)
            "dns_tunnel_txt_ratio": 0.5,  # TXT query ratio for tunneling
            "subdomain_length_threshold": 20  # Long subdomain threshold
        }
        
    def detect(self, time_window: timedelta = timedelta(minutes=5)) -> List[Anomaly]:
        """
        Run all Layer 7 detection rules and return detected anomalies.
        """
        anomalies = []
        now = datetime.now()
        
        for rule_name, rule_func in self.detection_rules.items():
            try:
                detected = rule_func(time_window)
                anomalies.extend(detected)
            except Exception as e:
                print(f"Error in rule {rule_name}: {e}")
                
        self.kg.anomalies.extend(anomalies)
        return anomalies
    
    def _detect_login_flood(self, time_window: timedelta) -> List[Anomaly]:
        """
        Detect login flood attacks.
        
        Rule: High number of failed login attempts from same session or identity.
        """
        anomalies = []
        now = datetime.now()
        
        for session_id, session in self.kg.sessions.items():
            if session.failed_logins > self.thresholds["login_failures_per_session"]:
                # Calculate score based on failure count
                score = min(1.0, session.failed_logins / (self.thresholds["login_failures_per_session"] * 2))
                
                anomaly = Anomaly(
                    anomaly_id=f"login_flood_{session_id}_{int(now.timestamp())}",
                    anomaly_type="LoginFloodAnomaly",
                    score=score,
                    confidence=0.85,
                    related_requests=[],
                    related_sessions=[f"session_{session_id}"],
                    timestamp=now,
                    attack_type=Layer7AttackType.LOGIN_FLOOD,
                    severity="high" if score > 0.7 else "medium",
                    explanation=f"Session {session_id} has {session.failed_logins} failed login attempts",
                    target_endpoint="/login",
                    evidence=[
                        f"Failed logins: {session.failed_logins}",
                        f"Session identity: {session.identity}",
                        f"IP address: {session.ip_address}"
                    ]
                )
                anomalies.append(anomaly)
                
        return anomalies
    
    def _detect_http_flood(self, time_window: timedelta) -> List[Anomaly]:
        """
        Detect HTTP flood attacks.
        
        Rule: Abnormal request rate per session targeting same endpoint.
        """
        anomalies = []
        now = datetime.now()
        
        session_metrics = self.kg.calculate_session_metrics()
        
        for session_id, metrics in session_metrics.items():
            rps = metrics["requests_per_second"]
            
            if rps > self.thresholds["requests_per_second_per_session"]:
                score = min(1.0, rps / (self.thresholds["requests_per_second_per_session"] * 2))
                
                # Get most targeted endpoint
                endpoints = list(self.kg.session_stats.get(session_id.replace("session_", ""), {}).get("endpoints_visited", set()))
                target_endpoint = endpoints[0] if endpoints else "unknown"
                
                anomaly = Anomaly(
                    anomaly_id=f"http_flood_{session_id}_{int(now.timestamp())}",
                    anomaly_type="HTTPFloodAnomaly",
                    score=score,
                    confidence=0.80,
                    related_requests=[],
                    related_sessions=[session_id],
                    timestamp=now,
                    attack_type=Layer7AttackType.HTTP_FLOOD,
                    severity="high" if score > 0.7 else "medium",
                    explanation=f"Session {session_id} has abnormal request rate: {rps:.1f} req/s",
                    target_endpoint=target_endpoint,
                    evidence=[
                        f"Requests per second: {rps:.1f}",
                        f"Total requests: {metrics['request_count']}",
                        f"Navigation diversity: {metrics['navigation_diversity']:.2f}"
                    ]
                )
                anomalies.append(anomaly)
                
        return anomalies
    
    def _detect_bot_behavior(self, time_window: timedelta) -> List[Anomaly]:
        """
        Detect bot-like behavior patterns.
        
        Rule: Low variability in headers, fingerprint, or navigation patterns.
        """
        anomalies = []
        now = datetime.now()
        
        for profile_id, profile in self.kg.behavior_profiles.items():
            is_suspicious = (
                profile.header_variability < self.thresholds["header_variability_threshold"] or
                profile.fingerprint_variability < self.thresholds["fingerprint_variability_threshold"] or
                profile.navigation_diversity < self.thresholds["navigation_diversity_threshold"]
            )
            
            if is_suspicious:
                score = 1.0 - min(
                    profile.header_variability,
                    profile.fingerprint_variability,
                    profile.navigation_diversity
                )
                
                anomaly = Anomaly(
                    anomaly_id=f"bot_{profile_id}_{int(now.timestamp())}",
                    anomaly_type="BotBehaviorAnomaly",
                    score=score,
                    confidence=0.75,
                    related_requests=[],
                    related_sessions=[f"session_{profile.session_id}"],
                    timestamp=now,
                    attack_type=Layer7AttackType.BOT_ATTACK,
                    severity="medium",
                    explanation=f"Session {profile.session_id} exhibits bot-like behavior",
                    evidence=[
                        f"Header variability: {profile.header_variability:.2f}",
                        f"Fingerprint variability: {profile.fingerprint_variability:.2f}",
                        f"Navigation diversity: {profile.navigation_diversity:.2f}"
                    ]
                )
                anomalies.append(anomaly)
                
        return anomalies
    
    def _detect_low_session_value(self, time_window: timedelta) -> List[Anomaly]:
        """
        Detect sessions with high request count but low value.
        
        Rule: High request count with low session value indicates API abuse.
        """
        anomalies = []
        now = datetime.now()
        
        session_metrics = self.kg.calculate_session_metrics()
        
        for session_id, metrics in session_metrics.items():
            session = self.kg.sessions.get(session_id.replace("session_", ""))
            if not session:
                continue
                
            # Calculate session value based on behavior
            session_value = metrics["navigation_diversity"] * (1 - metrics["error_count"] / max(metrics["request_count"], 1))
            
            if (metrics["request_count"] > 50 and 
                session_value < self.thresholds["session_value_threshold"]):
                
                score = 1.0 - session_value
                
                anomaly = Anomaly(
                    anomaly_id=f"low_value_{session_id}_{int(now.timestamp())}",
                    anomaly_type="LowSessionValueAnomaly",
                    score=score,
                    confidence=0.70,
                    related_requests=[],
                    related_sessions=[session_id],
                    timestamp=now,
                    attack_type=Layer7AttackType.API_ABUSE,
                    severity="medium",
                    explanation=f"Session {session_id} has high requests but low value",
                    evidence=[
                        f"Request count: {metrics['request_count']}",
                        f"Session value: {session_value:.2f}",
                        f"Navigation diversity: {metrics['navigation_diversity']:.2f}"
                    ]
                )
                anomalies.append(anomaly)
                
        return anomalies
    
    def _detect_expensive_endpoint_burst(self, time_window: timedelta) -> List[Anomaly]:
        """
        Detect burst of requests to computationally expensive endpoints.
        
        Rule: High request rate to endpoints with high computational cost.
        """
        anomalies = []
        now = datetime.now()
        
        endpoint_metrics = self.kg.calculate_endpoint_metrics()
        
        for endpoint_path, metrics in endpoint_metrics.items():
            endpoint = self.kg.endpoints.get(endpoint_path)
            if not endpoint:
                continue
                
            if (endpoint.computational_cost > 0.7 and 
                metrics["requests_per_second"] > self.thresholds["expensive_endpoint_rps"]):
                
                score = min(1.0, metrics["requests_per_second"] / (self.thresholds["expensive_endpoint_rps"] * 2))
                score *= endpoint.computational_cost
                
                anomaly = Anomaly(
                    anomaly_id=f"expensive_{endpoint_path.replace('/', '_')}_{int(now.timestamp())}",
                    anomaly_type="ExpensiveEndpointBurstAnomaly",
                    score=score,
                    confidence=0.90,
                    related_requests=[],
                    related_sessions=list(metrics["unique_sessions"])[:10],
                    timestamp=now,
                    attack_type=Layer7AttackType.HTTP_FLOOD,
                    severity="high" if score > 0.7 else "medium",
                    explanation=f"High request rate to expensive endpoint {endpoint_path}",
                    target_endpoint=endpoint_path,
                    evidence=[
                        f"Requests per second: {metrics['requests_per_second']:.1f}",
                        f"Computational cost: {endpoint.computational_cost:.2f}",
                        f"Unique sessions: {metrics['unique_sessions']}"
                    ]
                )
                anomalies.append(anomaly)
                
        return anomalies
    
    def _detect_latency_increase(self, time_window: timedelta) -> List[Anomaly]:
        """
        Detect significant latency increase on endpoints.
        
        Rule: Response time significantly higher than average indicates attack impact.
        """
        anomalies = []
        now = datetime.now()
        
        endpoint_metrics = self.kg.calculate_endpoint_metrics()
        
        for endpoint_path, metrics in endpoint_metrics.items():
            endpoint = self.kg.endpoints.get(endpoint_path)
            if not endpoint:
                continue
                
            if endpoint.average_response_time_ms > 0:
                latency_ratio = metrics["avg_response_time_ms"] / endpoint.average_response_time_ms
                
                if latency_ratio > self.thresholds["latency_multiplier"]:
                    score = min(1.0, latency_ratio / 5)
                    
                    anomaly = Anomaly(
                        anomaly_id=f"latency_{endpoint_path.replace('/', '_')}_{int(now.timestamp())}",
                        anomaly_type="LatencyIncreaseAnomaly",
                        score=score,
                        confidence=0.60,
                        related_requests=[],
                        related_sessions=[],
                        timestamp=now,
                        attack_type=Layer7AttackType.HTTP_FLOOD,
                        severity="medium",
                        explanation=f"Significant latency increase on {endpoint_path}",
                        target_endpoint=endpoint_path,
                        evidence=[
                            f"Current avg response time: {metrics['avg_response_time_ms']:.0f}ms",
                            f"Baseline response time: {endpoint.average_response_time_ms}ms",
                            f"Latency multiplier: {latency_ratio:.1f}x"
                        ]
                    )
                    anomalies.append(anomaly)
                    
        return anomalies
    
    def _detect_repetitive_route(self, time_window: timedelta) -> List[Anomaly]:
        """
        Detect high repetition of same route with low navigation diversity.
        
        Rule: Sessions repeatedly hitting same endpoint with low diversity.
        """
        anomalies = []
        now = datetime.now()
        
        session_metrics = self.kg.calculate_session_metrics()
        
        for session_id, metrics in session_metrics.items():
            if (metrics["navigation_diversity"] < self.thresholds["navigation_diversity_threshold"] and
                metrics["request_count"] > 30):
                
                score = 1.0 - metrics["navigation_diversity"]
                
                anomaly = Anomaly(
                    anomaly_id=f"repetitive_{session_id}_{int(now.timestamp())}",
                    anomaly_type="RepetitiveRouteAnomaly",
                    score=score,
                    confidence=0.70,
                    related_requests=[],
                    related_sessions=[session_id],
                    timestamp=now,
                    attack_type=Layer7AttackType.BOT_ATTACK,
                    severity="medium",
                    explanation=f"Session {session_id} shows repetitive route pattern",
                    evidence=[
                        f"Navigation diversity: {metrics['navigation_diversity']:.2f}",
                        f"Request count: {metrics['request_count']}",
                        f"Unique endpoints: {metrics['unique_endpoints']}"
                    ]
                )
                anomalies.append(anomaly)
                
        return anomalies
    
    def _detect_slow_request(self, time_window: timedelta) -> List[Anomaly]:
        """
        Detect slow request attacks (Slowloris, RUDY).
        
        Rule: Very slow requests consuming server resources.
        """
        anomalies = []
        now = datetime.now()
        
        for entity_id, entity in self.kg.entities.items():
            if entity.entity_type == EntityType.HTTP_REQUEST:
                response_time = entity.properties.get("response_time_ms", 0)
                method = entity.properties.get("method", "")
                
                if response_time > self.thresholds["slow_request_ms"]:
                    score = min(1.0, response_time / (self.thresholds["slow_request_ms"] * 2))
                    
                    anomaly = Anomaly(
                        anomaly_id=f"slow_{entity_id}_{int(now.timestamp())}",
                        anomaly_type="SlowRequestAnomaly",
                        score=score,
                        confidence=0.75,
                        related_requests=[entity_id],
                        related_sessions=[],
                        timestamp=now,
                        attack_type=Layer7AttackType.SLOW_REQUEST,
                        severity="high" if score > 0.7 else "medium",
                        explanation=f"Slow request detected: {response_time}ms response time",
                        target_endpoint=entity.properties.get("endpoint", ""),
                        evidence=[
                            f"Response time: {response_time}ms",
                            f"Method: {method}",
                            f"Threshold: {self.thresholds['slow_request_ms']}ms"
                        ]
                    )
                    anomalies.append(anomaly)
                    
        return anomalies
    
    def _detect_scraping(self, time_window: timedelta) -> List[Anomaly]:
        """
        Detect aggressive web scraping.
        
        Rule: Systematic access to many endpoints with bot-like patterns.
        """
        anomalies = []
        now = datetime.now()
        
        session_metrics = self.kg.calculate_session_metrics()
        
        for session_id, metrics in session_metrics.items():
            if metrics["unique_endpoints"] > self.thresholds["scraping_endpoints"]:
                # Check if behavior is bot-like
                profile_id = session_id.replace("session_", "")
                profile = self.kg.behavior_profiles.get(profile_id)
                
                is_bot = profile and profile.is_bot_like
                
                if is_bot or metrics["navigation_diversity"] > 0.8:
                    score = min(1.0, metrics["unique_endpoints"] / (self.thresholds["scraping_endpoints"] * 2))
                    
                    anomaly = Anomaly(
                        anomaly_id=f"scraping_{session_id}_{int(now.timestamp())}",
                        anomaly_type="ScrapingAnomaly",
                        score=score,
                        confidence=0.80,
                        related_requests=[],
                        related_sessions=[session_id],
                        timestamp=now,
                        attack_type=Layer7AttackType.SCRAPING,
                        severity="medium",
                        explanation=f"Session {session_id} shows aggressive scraping behavior",
                        evidence=[
                            f"Unique endpoints visited: {metrics['unique_endpoints']}",
                            f"Request count: {metrics['request_count']}",
                            f"Is bot-like: {is_bot}"
                        ]
                    )
                    anomalies.append(anomaly)
                    
        return anomalies
    
    def _detect_api_abuse(self, time_window: timedelta) -> List[Anomaly]:
        """
        Detect API abuse attacks.
        
        Rule: High error rates or abuse patterns on API endpoints.
        """
        anomalies = []
        now = datetime.now()
        
        endpoint_metrics = self.kg.calculate_endpoint_metrics()
        
        for endpoint_path, metrics in endpoint_metrics.items():
            # Check if it's an API endpoint
            if "/api/" in endpoint_path or "/graphql" in endpoint_path:
                if metrics["error_rate"] > self.thresholds["api_error_rate"]:
                    score = min(1.0, metrics["error_rate"] * 2)
                    
                    anomaly = Anomaly(
                        anomaly_id=f"api_abuse_{endpoint_path.replace('/', '_')}_{int(now.timestamp())}",
                        anomaly_type="APIAbuseAnomaly",
                        score=score,
                        confidence=0.75,
                        related_requests=[],
                        related_sessions=list(metrics["unique_sessions"])[:10],
                        timestamp=now,
                        attack_type=Layer7AttackType.API_ABUSE,
                        severity="medium",
                        explanation=f"High error rate on API endpoint {endpoint_path}",
                        target_endpoint=endpoint_path,
                        evidence=[
                            f"Error rate: {metrics['error_rate']:.2%}",
                            f"Request count: {metrics['request_count']}",
                            f"Requests per second: {metrics['requests_per_second']:.1f}"
                        ]
                    )
                    anomalies.append(anomaly)
                    
        return anomalies
    
    def _detect_qname_randomization(self, time_window: timedelta) -> List[Anomaly]:
        """
        Detect DNS QNAME randomization attacks (Random Subdomain Attack).
        
        Rule: High volume of queries with randomized subdomain prefixes
        targeting the same base domain. Used to bypass DNS-based rate limiting
        and flood DNS resolvers.
        
        Attack Pattern:
        - Random subdomain names (e.g., a7x9b2.example.com, k3m8n1.example.com)
        - High entropy in subdomain labels
        - Same base domain targeted repeatedly
        - Often uses DNSSEC-enabled domains to maximize resolver workload
        """
        anomalies = []
        now = datetime.now()
        
        dns_metrics = self.kg.calculate_dns_metrics()
        
        for src_ip, metrics in dns_metrics.items():
            # Check for high random subdomain ratio
            if (metrics["random_subdomain_ratio"] > self.thresholds["random_subdomain_ratio"] and
                metrics["query_count"] > 50):
                
                score = min(1.0, metrics["random_subdomain_ratio"] * 1.5)
                
                # Find the most targeted domain
                targeted_domains = list(self.kg.dns_stats[src_ip]["unique_domains"])
                primary_domain = targeted_domains[0] if targeted_domains else "unknown"
                
                anomaly = Anomaly(
                    anomaly_id=f"qname_random_{src_ip.replace('.', '_')}_{int(now.timestamp())}",
                    anomaly_type="QNameRandomizationAnomaly",
                    score=score,
                    confidence=0.85,
                    related_requests=[],
                    related_sessions=[],
                    timestamp=now,
                    attack_type=Layer7AttackType.QNAME_RANDOMIZATION,
                    severity="high" if score > 0.7 else "medium",
                    explanation=f"Source IP {src_ip} sending randomized DNS queries to {primary_domain}",
                    target_endpoint=f"DNS:{primary_domain}",
                    evidence=[
                        f"Random subdomain ratio: {metrics['random_subdomain_ratio']:.2%}",
                        f"Total queries: {metrics['query_count']}",
                        f"Unique subdomains: {metrics['unique_subdomains']}",
                        f"Average subdomain entropy: {metrics['subdomain_entropy_avg']:.2f}",
                        f"Queries per second: {metrics['queries_per_second']:.1f}",
                        f"Target domains: {len(targeted_domains)}"
                    ]
                )
                anomalies.append(anomaly)
        
        # Also check per-domain for distributed attacks
        domain_metrics = self.kg.calculate_domain_metrics()
        for domain, metrics in domain_metrics.items():
            if metrics["unique_subdomains"] > self.thresholds["unique_subdomains_per_domain"]:
                score = min(1.0, metrics["unique_subdomains"] / (self.thresholds["unique_subdomains_per_domain"] * 2))
                
                anomaly = Anomaly(
                    anomaly_id=f"qname_random_domain_{domain.replace('.', '_')}_{int(now.timestamp())}",
                    anomaly_type="QNameRandomizationAnomaly",
                    score=score,
                    confidence=0.80,
                    related_requests=[],
                    related_sessions=[],
                    timestamp=now,
                    attack_type=Layer7AttackType.QNAME_RANDOMIZATION,
                    severity="high" if score > 0.7 else "medium",
                    explanation=f"Domain {domain} receiving randomized subdomain queries from {metrics['unique_src_ips']} sources",
                    target_endpoint=f"DNS:{domain}",
                    evidence=[
                        f"Unique subdomains: {metrics['unique_subdomains']}",
                        f"Total queries: {metrics['query_count']}",
                        f"Unique source IPs: {metrics['unique_src_ips']}",
                        f"Queries per second: {metrics['queries_per_second']:.1f}"
                    ]
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_nxdomain_flood(self, time_window: timedelta) -> List[Anomaly]:
        """
        Detect NXDOMAIN flood attacks.
        
        Rule: High ratio of NXDOMAIN responses indicating queries for
        non-existent domains. Used to flood DNS resolvers with negative
        responses and consume cache resources.
        
        Attack Pattern:
        - High NXDOMAIN response ratio
        - Queries for non-existent domains
        - Can target authoritative servers or recursive resolvers
        - Consumes resolver cache and CPU
        """
        anomalies = []
        now = datetime.now()
        
        dns_metrics = self.kg.calculate_dns_metrics()
        
        for src_ip, metrics in dns_metrics.items():
            if (metrics["nxdomain_ratio"] > self.thresholds["nxdomain_ratio"] and
                metrics["query_count"] > 30):
                
                score = min(1.0, metrics["nxdomain_ratio"] * 1.5)
                
                anomaly = Anomaly(
                    anomaly_id=f"nxdomain_flood_{src_ip.replace('.', '_')}_{int(now.timestamp())}",
                    anomaly_type="NXDOMAINFloodAnomaly",
                    score=score,
                    confidence=0.85,
                    related_requests=[],
                    related_sessions=[],
                    timestamp=now,
                    attack_type=Layer7AttackType.NXDOMAIN_FLOOD,
                    severity="high" if score > 0.7 else "medium",
                    explanation=f"Source IP {src_ip} generating high NXDOMAIN ratio ({metrics['nxdomain_ratio']:.1%})",
                    target_endpoint="DNS:Resolver",
                    evidence=[
                        f"NXDOMAIN ratio: {metrics['nxdomain_ratio']:.2%}",
                        f"NXDOMAIN count: {metrics['nxdomain_count']}",
                        f"Total queries: {metrics['query_count']}",
                        f"Unique domains queried: {metrics['unique_domains']}",
                        f"Queries per second: {metrics['queries_per_second']:.1f}"
                    ]
                )
                anomalies.append(anomaly)
        
        # Check per-domain NXDOMAIN patterns
        domain_metrics = self.kg.calculate_domain_metrics()
        for domain, metrics in domain_metrics.items():
            if metrics["nxdomain_ratio"] > self.thresholds["nxdomain_ratio"]:
                score = min(1.0, metrics["nxdomain_ratio"])
                
                anomaly = Anomaly(
                    anomaly_id=f"nxdomain_domain_{domain.replace('.', '_')}_{int(now.timestamp())}",
                    anomaly_type="NXDOMAINFloodAnomaly",
                    score=score,
                    confidence=0.75,
                    related_requests=[],
                    related_sessions=[],
                    timestamp=now,
                    attack_type=Layer7AttackType.NXDOMAIN_FLOOD,
                    severity="medium",
                    explanation=f"Domain {domain} has high NXDOMAIN query ratio",
                    target_endpoint=f"DNS:{domain}",
                    evidence=[
                        f"NXDOMAIN ratio: {metrics['nxdomain_ratio']:.2%}",
                        f"Total queries: {metrics['query_count']}",
                        f"Unique source IPs: {metrics['unique_src_ips']}"
                    ]
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_dns_water_torture(self, time_window: timedelta) -> List[Anomaly]:
        """
        Detect DNS Water Torture attacks (Slow Drip DNS Attack).
        
        Rule: Low and steady rate of DNS queries spread across time,
        targeting a specific domain with random subdomains. Designed to
        fly under rate limiting thresholds while maintaining persistent
        pressure on DNS infrastructure.
        
        Attack Pattern:
        - Consistent low-rate queries (below typical thresholds)
        - Random subdomains to bypass cache
        - Extended duration (hours to days)
        - Targets authoritative servers
        """
        anomalies = []
        now = datetime.now()
        
        # Analyze query patterns over extended time window
        extended_window = timedelta(hours=1)
        
        domain_metrics = self.kg.calculate_domain_metrics()
        
        for domain, metrics in domain_metrics.items():
            # Water torture: steady low rate with many unique subdomains
            # Key indicator: high unique subdomains but moderate QPS
            if (metrics["unique_subdomains"] > 100 and
                metrics["queries_per_second"] < 50 and
                metrics["queries_per_second"] > 1):
                
                # Calculate "steadiness" - consistent rate over time
                timestamps = self.kg.domain_stats[domain]["timestamps"]
                if len(timestamps) >= 10:
                    time_diffs = np.diff([t.timestamp() for t in sorted(timestamps)])
                    interval_std = np.std(time_diffs) if len(time_diffs) > 1 else 0
                    interval_avg = np.mean(time_diffs) if len(time_diffs) > 0 else 0
                    
                    # Low std deviation indicates steady rate
                    steadiness = 1.0 - min(1.0, interval_std / max(interval_avg, 1))
                    
                    if steadiness > 0.5:  # Relatively steady rate
                        score = min(1.0, metrics["unique_subdomains"] / 500) * steadiness
                        
                        anomaly = Anomaly(
                            anomaly_id=f"water_torture_{domain.replace('.', '_')}_{int(now.timestamp())}",
                            anomaly_type="DNSWaterTortureAnomaly",
                            score=score,
                            confidence=0.70,
                            related_requests=[],
                            related_sessions=[],
                            timestamp=now,
                            attack_type=Layer7AttackType.DNS_WATER_TORTURE,
                            severity="medium",
                            explanation=f"Domain {domain} under slow-drip DNS attack with steady query rate",
                            target_endpoint=f"DNS:{domain}",
                            evidence=[
                                f"Unique subdomains: {metrics['unique_subdomains']}",
                                f"Queries per second: {metrics['queries_per_second']:.2f} (low but steady)",
                                f"Attack steadiness: {steadiness:.2%}",
                                f"Total queries: {metrics['query_count']}",
                                f"Unique source IPs: {metrics['unique_src_ips']}"
                            ]
                        )
                        anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_dns_amplification(self, time_window: timedelta) -> List[Anomaly]:
        """
        Detect DNS amplification attack patterns.
        
        Rule: Large DNS responses relative to query size, indicating
        potential amplification. Also detects ANY queries and high
        response sizes typical of amplification attacks.
        
        Attack Pattern:
        - Small queries generating large responses
        - Use of ANY, TXT, or DNSSEC record types
        - High amplification factor (response/query size ratio)
        - Spoofed source IPs (detected via asymmetric traffic)
        """
        anomalies = []
        now = datetime.now()
        
        for query_id, query in self.kg.dns_queries.items():
            # Check for amplification indicators
            if query.query_size > 0 and query.response_size > 0:
                amplification_factor = query.response_size / query.query_size
                
                # High amplification factor (normal is usually < 10)
                if (amplification_factor > 10 or 
                    query.response_size > self.thresholds["dns_response_size_bytes"]):
                    
                    score = min(1.0, amplification_factor / 50)
                    
                    anomaly = Anomaly(
                        anomaly_id=f"dns_amp_{query_id}_{int(now.timestamp())}",
                        anomaly_type="DNSAmplificationAnomaly",
                        score=score,
                        confidence=0.80,
                        related_requests=[f"dns_query_{query_id}"],
                        related_sessions=[],
                        timestamp=now,
                        attack_type=Layer7AttackType.DNS_AMPLIFICATION,
                        severity="high" if score > 0.7 else "medium",
                        explanation=f"DNS amplification detected: {amplification_factor:.1f}x amplification factor",
                        target_endpoint=f"DNS:{query.qname}",
                        evidence=[
                            f"Amplification factor: {amplification_factor:.1f}x",
                            f"Query size: {query.query_size} bytes",
                            f"Response size: {query.response_size} bytes",
                            f"Query type: {query.qtype}",
                            f"Source IP: {query.src_ip}",
                            f"DNS server: {query.dst_ip}"
                        ]
                    )
                    anomalies.append(anomaly)
        
        # Check for ANY queries (commonly used in amplification)
        for src_ip, stats in self.kg.dns_stats.items():
            if "ANY" in stats["qtypes"]:
                any_query_count = sum(1 for q in self.kg.dns_queries.values() 
                                     if q.src_ip == src_ip and q.qtype == "ANY")
                if any_query_count > 5:
                    anomaly = Anomaly(
                        anomaly_id=f"dns_amp_any_{src_ip.replace('.', '_')}_{int(now.timestamp())}",
                        anomaly_type="DNSAmplificationAnomaly",
                        score=0.75,
                        confidence=0.85,
                        related_requests=[],
                        related_sessions=[],
                        timestamp=now,
                        attack_type=Layer7AttackType.DNS_AMPLIFICATION,
                        severity="high",
                        explanation=f"Source {src_ip} sending DNS ANY queries (amplification indicator)",
                        target_endpoint="DNS:Resolver",
                        evidence=[
                            f"ANY query count: {any_query_count}",
                            f"Source IP: {src_ip}",
                            f"ANY queries are commonly used for DNS amplification attacks"
                        ]
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_phantom_domain(self, time_window: timedelta) -> List[Anomaly]:
        """
        Detect Phantom Domain attacks.
        
        Rule: Queries to domains that don't exist or are configured
        to return specific responses, used to tie up resolver resources.
        Attackers register domains with slow or non-responsive authoritative
        servers to exhaust resolver resources.
        
        Attack Pattern:
        - Queries to domains with slow/non-responsive auth servers
        - High timeout rates
        - Multiple concurrent queries to same phantom domain
        - Resolver resource exhaustion
        """
        anomalies = []
        now = datetime.now()
        
        domain_metrics = self.kg.calculate_domain_metrics()
        
        for domain, metrics in domain_metrics.items():
            # Check for slow response times and timeouts
            domain_queries = [q for q in self.kg.dns_queries.values() 
                             if q.get_base_domain() == domain]
            
            if domain_queries:
                avg_response_time = np.mean([q.response_time_ms for q in domain_queries])
                timeout_count = sum(1 for q in domain_queries if q.response_code == "SERVFAIL" or q.response_time_ms > 5000)
                timeout_ratio = timeout_count / len(domain_queries)
                
                # Phantom domain indicators
                if (avg_response_time > 2000 or timeout_ratio > 0.3) and metrics["query_count"] > 20:
                    score = min(1.0, timeout_ratio * 2)
                    
                    anomaly = Anomaly(
                        anomaly_id=f"phantom_domain_{domain.replace('.', '_')}_{int(now.timestamp())}",
                        anomaly_type="PhantomDomainAnomaly",
                        score=score,
                        confidence=0.70,
                        related_requests=[],
                        related_sessions=[],
                        timestamp=now,
                        attack_type=Layer7AttackType.PHANTOM_DOMAIN,
                        severity="medium",
                        explanation=f"Domain {domain} exhibiting phantom domain attack characteristics",
                        target_endpoint=f"DNS:{domain}",
                        evidence=[
                            f"Average response time: {avg_response_time:.0f}ms",
                            f"Timeout/SERVFAIL ratio: {timeout_ratio:.2%}",
                            f"Total queries: {metrics['query_count']}",
                            f"Unique source IPs affected: {metrics['unique_src_ips']}"
                        ]
                    )
                    anomalies.append(anomaly)
        
        return anomalies
    
    def _detect_dns_tunneling(self, time_window: timedelta) -> List[Anomaly]:
        """
        Detect DNS tunneling attacks.
        
        Rule: Unusual patterns in DNS queries indicating data exfiltration
        or command-and-control via DNS protocol.
        
        Attack Pattern:
        - Unusually long subdomain labels (encoded data)
        - High TXT record queries
        - Unusual query types for the domain
        - High entropy in query names
        - Low response sizes relative to query sizes
        """
        anomalies = []
        now = datetime.now()
        
        dns_metrics = self.kg.calculate_dns_metrics()
        
        for src_ip, metrics in dns_metrics.items():
            # Check for tunneling indicators
            stats = self.kg.dns_stats[src_ip]
            
            # High TXT query ratio
            txt_queries = sum(1 for q in self.kg.dns_queries.values() 
                             if q.src_ip == src_ip and q.qtype == "TXT")
            txt_ratio = txt_queries / max(metrics["query_count"], 1)
            
            # Long subdomain labels (encoded data)
            long_subdomains = sum(1 for s in stats["subdomains"] 
                                 if len(s) > self.thresholds["subdomain_length_threshold"])
            long_subdomain_ratio = long_subdomains / max(len(stats["subdomains"]), 1)
            
            # High entropy queries
            high_entropy_count = sum(1 for s in stats["subdomains"] 
                                    if self._calculate_entropy(s) > self.thresholds["dns_entropy_threshold"])
            high_entropy_ratio = high_entropy_count / max(len(stats["subdomains"]), 1)
            
            # Combined tunneling score
            tunneling_score = (txt_ratio * 0.3 + long_subdomain_ratio * 0.4 + high_entropy_ratio * 0.3)
            
            if tunneling_score > 0.4 and metrics["query_count"] > 20:
                score = min(1.0, tunneling_score * 2)
                
                anomaly = Anomaly(
                    anomaly_id=f"dns_tunnel_{src_ip.replace('.', '_')}_{int(now.timestamp())}",
                    anomaly_type="DNSTunnelingAnomaly",
                    score=score,
                    confidence=0.75,
                    related_requests=[],
                    related_sessions=[],
                    timestamp=now,
                    attack_type=Layer7AttackType.DNS_TUNNELING,
                    severity="high" if score > 0.7 else "medium",
                    explanation=f"Source IP {src_ip} exhibiting DNS tunneling behavior",
                    target_endpoint="DNS:Tunnel",
                    evidence=[
                        f"TXT query ratio: {txt_ratio:.2%}",
                        f"Long subdomain ratio: {long_subdomain_ratio:.2%}",
                        f"High entropy subdomain ratio: {high_entropy_ratio:.2%}",
                        f"Total queries: {metrics['query_count']}",
                        f"Average subdomain length: {metrics['avg_subdomain_length']:.1f}",
                        f"Subdomain entropy avg: {metrics['subdomain_entropy_avg']:.2f}"
                    ]
                )
                anomalies.append(anomaly)
        
        return anomalies
    
    def _calculate_entropy(self, string: str) -> float:
        """Calculate Shannon entropy of a string."""
        if not string:
            return 0.0
        counts = Counter(string.lower())
        probs = [c/len(string) for c in counts.values()]
        return -sum(p * math.log2(p) for p in probs)


# =============================================================================
# EXPLAINABILITY ENGINE
# =============================================================================

class ExplainabilityEngine:
    """
    Engine for generating human-readable explanations of detected anomalies.
    """
    
    @staticmethod
    def generate_explanation(anomaly: Anomaly) -> str:
        """Generate a detailed explanation for an anomaly."""
        explanation_parts = [
            f"## Anomaly Report: {anomaly.anomaly_type}",
            f"",
            f"**Severity:** {anomaly.severity.upper()}",
            f"**Confidence:** {anomaly.confidence:.0%}",
            f"**Attack Type:** {anomaly.attack_type.value if anomaly.attack_type else 'Unknown'}",
            f"",
            f"### Summary",
            anomaly.explanation,
            f"",
            f"### Evidence"
        ]
        
        for evidence in anomaly.evidence:
            explanation_parts.append(f"- {evidence}")
            
        if anomaly.target_endpoint:
            explanation_parts.extend([
                f"",
                f"### Target Endpoint",
                f"- Path: {anomaly.target_endpoint}"
            ])
            
        if anomaly.related_sessions:
            explanation_parts.extend([
                f"",
                f"### Affected Sessions",
                f"- {len(anomaly.related_sessions)} session(s) involved"
            ])
            
        explanation_parts.extend([
            f"",
            f"### Recommended Actions"
        ])
        
        recommendations = ExplainabilityEngine._get_recommendations(anomaly)
        for rec in recommendations:
            explanation_parts.append(f"- {rec}")
            
        return "\n".join(explanation_parts)
    
    @staticmethod
    def _get_recommendations(anomaly: Anomaly) -> List[str]:
        """Get mitigation recommendations based on attack type."""
        recommendations = {
            Layer7AttackType.LOGIN_FLOOD: [
                "Implement CAPTCHA challenge on login page",
                "Enable rate limiting per identity (e.g., 5 attempts/minute)",
                "Add progressive delays after failed attempts",
                "Consider temporary account lockout"
            ],
            Layer7AttackType.HTTP_FLOOD: [
                "Enable rate limiting per session/IP",
                "Implement JavaScript challenge",
                "Review WAF rules for this endpoint",
                "Consider CDN caching for static content"
            ],
            Layer7AttackType.BOT_ATTACK: [
                "Implement bot detection (CAPTCHA, JavaScript challenge)",
                "Review User-Agent patterns",
                "Enable browser fingerprinting checks",
                "Consider bot management service"
            ],
            Layer7AttackType.API_ABUSE: [
                "Implement API rate limiting",
                "Add API key validation",
                "Review API authentication",
                "Consider request throttling"
            ],
            Layer7AttackType.SCRAPING: [
                "Implement robots.txt restrictions",
                "Add CAPTCHA challenges",
                "Monitor session patterns",
                "Consider data access limits"
            ],
            Layer7AttackType.SLOW_REQUEST: [
                "Configure connection timeouts",
                "Implement request body size limits",
                "Enable connection rate limiting",
                "Review server thread pool settings"
            ],
            # DNS Layer 7 Attack Mitigations
            Layer7AttackType.QNAME_RANDOMIZATION: [
                "Implement Response Rate Limiting (RRL) on DNS servers",
                "Enable DNS query rate limiting per source IP",
                "Deploy DNS firewall with random subdomain detection",
                "Configure DNS cache to minimize upstream queries",
                "Consider DNSSEC to reduce amplification potential"
            ],
            Layer7AttackType.NXDOMAIN_FLOOD: [
                "Enable NXDOMAIN caching with appropriate TTL",
                "Implement Response Rate Limiting (RRL)",
                "Configure negative caching TTL",
                "Deploy DNS firewall with NXDOMAIN flood detection",
                "Monitor and rate-limit repetitive NXDOMAIN queries"
            ],
            Layer7AttackType.DNS_WATER_TORTURE: [
                "Implement DNS query rate limiting with sliding window",
                "Enable DNS response caching",
                "Deploy anycast DNS infrastructure",
                "Monitor long-duration low-rate query patterns",
                "Consider DNS load balancing across multiple servers"
            ],
            Layer7AttackType.DNS_AMPLIFICATION: [
                "Disable open DNS recursion on authoritative servers",
                "Block DNS ANY queries from external sources",
                "Implement source IP verification",
                "Configure Response Rate Limiting (RRL)",
                "Monitor for unusually large DNS responses"
            ],
            Layer7AttackType.PHANTOM_DOMAIN: [
                "Implement aggressive timeout settings for slow domains",
                "Configure concurrent query limits per domain",
                "Monitor for domains with consistently slow responses",
                "Implement fallback DNS servers",
                "Consider blocking known phantom domains"
            ],
            Layer7AttackType.DNS_TUNNELING: [
                "Deploy DNS tunneling detection solutions",
                "Monitor for unusually long DNS queries",
                "Block or rate-limit TXT record queries",
                "Implement DNS query length limits",
                "Analyze DNS traffic for encoded data patterns"
            ]
        }
        
        if anomaly.attack_type:
            return recommendations.get(anomaly.attack_type, ["Review and investigate the anomaly"])
        return ["Review and investigate the anomaly"]


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

def simulate_layer7_attack():
    """
    Simulate a Layer 7 DDoS attack scenario for demonstration.
    """
    print("=" * 70)
    print("Knowledge Graph-Based Layer 7 DDoS Detection Simulation")
    print("=" * 70)
    
    # Initialize knowledge graph
    kg = Layer7KnowledgeGraph()
    
    # Register endpoints
    print("\n[1] Registering application endpoints...")
    endpoints = [
        Endpoint("/login", computational_cost=0.8, is_cacheable=False, requires_auth=False, depends_on_db=True, criticality="high"),
        Endpoint("/api/products", computational_cost=0.6, is_cacheable=True, requires_auth=False, depends_on_db=True, criticality="medium"),
        Endpoint("/api/search", computational_cost=0.9, is_cacheable=False, requires_auth=False, depends_on_db=True, criticality="high"),
        Endpoint("/checkout", computational_cost=0.95, is_cacheable=False, requires_auth=True, depends_on_db=True, criticality="critical"),
        Endpoint("/static/js/app.js", computational_cost=0.1, is_cacheable=True, requires_auth=False, depends_on_db=False, criticality="low"),
    ]
    
    for endpoint in endpoints:
        kg.register_endpoint(endpoint)
        print(f"   Registered: {endpoint.path} (cost: {endpoint.computational_cost}, criticality: {endpoint.criticality})")
    
    # Simulate normal traffic
    print("\n[2] Adding normal traffic...")
    normal_requests = [
        HTTPRequest(
            request_id=f"normal_{i}",
            method="GET",
            path=f"/api/products/{i % 10}",
            endpoint="/api/products",
            src_ip=f"192.168.1.{i % 50}",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            session_id=f"session_{i % 20}",
            response_code=200,
            response_time_ms=50 + (i % 30),
            timestamp=datetime.now() - timedelta(seconds=i)
        )
        for i in range(100)
    ]
    
    for request in normal_requests:
        kg.add_http_request(request)
    
    print(f"   Added {len(normal_requests)} normal requests")
    print(f"   Graph nodes: {kg.graph.number_of_nodes()}")
    print(f"   Graph edges: {kg.graph.number_of_edges()}")
    
    # Simulate Layer 7 attack traffic
    print("\n[3] Simulating Layer 7 DDoS attacks...")
    
    # HTTP Flood attack
    attack_requests = [
        HTTPRequest(
            request_id=f"attack_http_{i}",
            method="GET",
            path="/api/search?q=test",
            endpoint="/api/search",
            src_ip=f"203.0.113.{i % 255}",
            user_agent="python-requests/2.28.0",  # Bot-like user agent
            session_id=f"attack_session_{i % 10}",
            response_code=200,
            response_time_ms=200 + (i % 50),
            timestamp=datetime.now()
        )
        for i in range(500)  # High volume
    ]
    
    # Login flood attack
    login_attack_requests = [
        HTTPRequest(
            request_id=f"attack_login_{i}",
            method="POST",
            path="/login",
            endpoint="/login",
            src_ip=f"198.51.100.{i % 100}",
            user_agent="curl/7.68.0",
            session_id=f"login_attack_session",
            response_code=401,  # Failed login
            response_time_ms=100,
            timestamp=datetime.now()
        )
        for i in range(50)
    ]
    
    # Update session with failed logins
    if "login_attack_session" in kg.sessions:
        kg.sessions["login_attack_session"].failed_logins = 50
        kg.sessions["login_attack_session"].login_attempts = 50
    
    # Add bot behavior profiles
    for i in range(10):
        profile = BehaviorProfile(
            profile_id=f"attack_profile_{i}",
            session_id=f"attack_session_{i}",
            header_variability=0.05,  # Very low - bot-like
            fingerprint_variability=0.02,
            navigation_diversity=0.1,
            request_interval_avg_ms=100,  # Very fast
            request_interval_std=5,  # Very consistent
            is_bot_like=True,
            pattern_type="malicious"
        )
        kg.update_behavior_profile(profile)
    
    for request in attack_requests + login_attack_requests:
        kg.add_http_request(request)
    
    print(f"   Added {len(attack_requests) + len(login_attack_requests)} attack requests")
    print(f"   Graph nodes: {kg.graph.number_of_nodes()}")
    print(f"   Graph edges: {kg.graph.number_of_edges()}")
    
    # Run anomaly detection
    print("\n[4] Running Layer 7 anomaly detection...")
    detector = Layer7AnomalyDetector(kg)
    anomalies = detector.detect()
    
    print(f"\n[5] Detection Results:")
    print(f"   Total anomalies detected: {len(anomalies)}")
    
    # Group by attack type
    attack_counts = defaultdict(int)
    for anomaly in anomalies:
        if anomaly.attack_type:
            attack_counts[anomaly.attack_type.value] += 1
    
    print("\n   Attack Type Distribution:")
    for attack_type, count in attack_counts.items():
        print(f"   - {attack_type}: {count}")
    
    # Display top anomalies with explanations
    print("\n   Top Anomalies (by score):")
    sorted_anomalies = sorted(anomalies, key=lambda x: x.score, reverse=True)[:3]
    
    for anomaly in sorted_anomalies:
        print(f"\n   {'='*50}")
        print(ExplainabilityEngine.generate_explanation(anomaly))
    
    # Endpoint metrics
    print("\n[6] Endpoint Metrics:")
    endpoint_metrics = kg.calculate_endpoint_metrics()
    for endpoint, metrics in endpoint_metrics.items():
        print(f"   {endpoint}:")
        print(f"      Requests: {metrics['request_count']}, RPS: {metrics['requests_per_second']:.1f}")
        print(f"      Avg response time: {metrics['avg_response_time_ms']:.0f}ms")
        print(f"      Error rate: {metrics['error_rate']:.1%}")
    
    # Export graph
    print("\n[7] Exporting knowledge graph...")
    export_data = {
        "nodes": [e.to_dict() for e in kg.entities.values()],
        "edges": [r.to_dict() for r in kg.relations],
        "anomalies": [a.to_entity().properties for a in kg.anomalies]
    }
    
    with open("layer7_knowledge_graph_export.json", "w") as f:
        json.dump(export_data, f, indent=2, default=str)
    
    print("   Exported to: layer7_knowledge_graph_export.json")
    
    return kg, anomalies


# =============================================================================
# SEMANTIC QUERY ENGINE - Layer 7 Specific Queries
# =============================================================================

class SemanticQueryEngine:
    """
    Engine for answering semantic questions about Layer 7 attacks.
    
    Supports queries like:
    - "Which endpoint is under attack?"
    - "What signals support this hypothesis?"
    - "What mitigation has the highest chance of success?"
    """
    
    def __init__(self, kg: Layer7KnowledgeGraph):
        self.kg = kg
        
    def query_endpoint_under_attack(self) -> Dict:
        """
        Answer: "Which endpoint is under attack?"
        
        Returns the endpoint with highest anomaly concentration.
        """
        endpoint_anomaly_count = defaultdict(lambda: {"count": 0, "anomalies": [], "severity_sum": 0})
        
        for anomaly in self.kg.anomalies:
            if anomaly.target_endpoint:
                endpoint_anomaly_count[anomaly.target_endpoint]["count"] += 1
                endpoint_anomaly_count[anomaly.target_endpoint]["anomalies"].append(anomaly)
                severity_val = {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(anomaly.severity, 2)
                endpoint_anomaly_count[anomaly.target_endpoint]["severity_sum"] += severity_val
        
        if not endpoint_anomaly_count:
            return {"status": "no_attack_detected", "endpoint": None, "confidence": 0}
        
        # Find endpoint with highest combined score
        top_endpoint = max(
            endpoint_anomaly_count.items(),
            key=lambda x: x[1]["count"] * x[1]["severity_sum"]
        )
        
        return {
            "status": "attack_detected",
            "endpoint": top_endpoint[0],
            "anomaly_count": top_endpoint[1]["count"],
            "anomalies": [
                {
                    "type": a.anomaly_type,
                    "attack_type": a.attack_type.value if a.attack_type else None,
                    "severity": a.severity,
                    "score": a.score
                }
                for a in top_endpoint[1]["anomalies"]
            ],
            "confidence": min(1.0, top_endpoint[1]["count"] * 0.2)
        }
    
    def query_attack_hypothesis_evidence(self, attack_type: Layer7AttackType) -> Dict:
        """
        Answer: "What signals support this attack hypothesis?"
        
        Returns all evidence supporting a specific attack type.
        """
        supporting_anomalies = [
            a for a in self.kg.anomalies
            if a.attack_type == attack_type
        ]
        
        if not supporting_anomalies:
            return {
                "attack_type": attack_type.value,
                "evidence_count": 0,
                "evidence": [],
                "confidence": 0
            }
        
        all_evidence = []
        for anomaly in supporting_anomalies:
            all_evidence.extend(anomaly.evidence)
        
        # Aggregate evidence by type
        evidence_by_type = defaultdict(list)
        for evidence in all_evidence:
            # Parse evidence type from string
            if "Failed logins" in evidence:
                evidence_by_type["authentication_failures"].append(evidence)
            elif "Requests per second" in evidence or "request rate" in evidence:
                evidence_by_type["rate_anomaly"].append(evidence)
            elif "variability" in evidence.lower() or "diversity" in evidence.lower():
                evidence_by_type["behavioral_anomaly"].append(evidence)
            elif "latency" in evidence.lower() or "response time" in evidence.lower():
                evidence_by_type["performance_impact"].append(evidence)
            elif "endpoint" in evidence.lower():
                evidence_by_type["endpoint_targeting"].append(evidence)
            else:
                evidence_by_type["other"].append(evidence)
        
        return {
            "attack_type": attack_type.value,
            "evidence_count": len(all_evidence),
            "anomaly_count": len(supporting_anomalies),
            "evidence_by_type": dict(evidence_by_type),
            "confidence": min(1.0, len(supporting_anomalies) * 0.25),
            "affected_sessions": list(set(
                s for a in supporting_anomalies for s in a.related_sessions
            ))[:20]
        }
    
    def query_best_mitigation(self, endpoint: str = None) -> Dict:
        """
        Answer: "What mitigation has the highest chance of reducing impact
        without blocking legitimate users?"
        
        Returns context-aware mitigation recommendations.
        """
        relevant_anomalies = [
            a for a in self.kg.anomalies
            if endpoint is None or a.target_endpoint == endpoint
        ]
        
        if not relevant_anomalies:
            return {
                "status": "no_mitigation_needed",
                "recommendations": []
            }
        
        # Analyze attack patterns
        attack_types = defaultdict(int)
        for anomaly in relevant_anomalies:
            if anomaly.attack_type:
                attack_types[anomaly.attack_type] += 1
        
        # Get endpoint characteristics
        endpoint_info = None
        if endpoint and endpoint in self.kg.endpoints:
            ep = self.kg.endpoints[endpoint]
            endpoint_info = {
                "path": endpoint,
                "computational_cost": ep.computational_cost,
                "is_cacheable": ep.is_cacheable,
                "requires_auth": ep.requires_auth,
                "criticality": ep.criticality
            }
        
        # Generate context-aware recommendations
        recommendations = self._generate_context_aware_recommendations(
            attack_types, endpoint_info, relevant_anomalies
        )
        
        return {
            "status": "recommendations_available",
            "endpoint": endpoint,
            "endpoint_info": endpoint_info,
            "attack_types_detected": {k.value: v for k, v in attack_types.items()},
            "recommendations": recommendations,
            "confidence": min(1.0, len(relevant_anomalies) * 0.15)
        }
    
    def _generate_context_aware_recommendations(
        self, 
        attack_types: Dict, 
        endpoint_info: Dict,
        anomalies: List[Anomaly]
    ) -> List[Dict]:
        """Generate recommendations based on attack context."""
        recommendations = []
        
        for attack_type, count in attack_types.items():
            base_recs = {
                Layer7AttackType.LOGIN_FLOOD: [
                    {
                        "action": "enable_captcha",
                        "description": "Add CAPTCHA challenge to login form",
                        "impact_on_legitimate": "low",
                        "effectiveness": "high",
                        "implementation_effort": "low"
                    },
                    {
                        "action": "rate_limit_identity",
                        "description": "Rate limit by identity (email/username) not just IP",
                        "impact_on_legitimate": "low",
                        "effectiveness": "high",
                        "implementation_effort": "medium"
                    },
                    {
                        "action": "progressive_delay",
                        "description": "Add progressive delays after failed attempts",
                        "impact_on_legitimate": "low",
                        "effectiveness": "medium",
                        "implementation_effort": "low"
                    }
                ],
                Layer7AttackType.HTTP_FLOOD: [
                    {
                        "action": "javascript_challenge",
                        "description": "Implement JavaScript challenge for suspicious sessions",
                        "impact_on_legitimate": "medium",
                        "effectiveness": "high",
                        "implementation_effort": "medium"
                    },
                    {
                        "action": "rate_limit_session",
                        "description": "Rate limit per session token",
                        "impact_on_legitimate": "low",
                        "effectiveness": "high",
                        "implementation_effort": "low"
                    },
                    {
                        "action": "enable_caching",
                        "description": "Enable CDN caching for cacheable endpoints",
                        "impact_on_legitimate": "positive",
                        "effectiveness": "medium",
                        "implementation_effort": "low"
                    }
                ],
                Layer7AttackType.BOT_ATTACK: [
                    {
                        "action": "browser_fingerprinting",
                        "description": "Implement browser fingerprinting checks",
                        "impact_on_legitimate": "low",
                        "effectiveness": "high",
                        "implementation_effort": "medium"
                    },
                    {
                        "action": "behavior_analysis",
                        "description": "Enable behavioral analysis for session patterns",
                        "impact_on_legitimate": "low",
                        "effectiveness": "high",
                        "implementation_effort": "high"
                    }
                ],
                Layer7AttackType.API_ABUSE: [
                    {
                        "action": "api_key_validation",
                        "description": "Require API key for endpoint access",
                        "impact_on_legitimate": "medium",
                        "effectiveness": "high",
                        "implementation_effort": "medium"
                    },
                    {
                        "action": "api_rate_limiting",
                        "description": "Implement tiered API rate limiting",
                        "impact_on_legitimate": "low",
                        "effectiveness": "high",
                        "implementation_effort": "low"
                    }
                ],
                Layer7AttackType.SCRAPING: [
                    {
                        "action": "data_access_limits",
                        "description": "Limit data returned per request",
                        "impact_on_legitimate": "low",
                        "effectiveness": "medium",
                        "implementation_effort": "low"
                    },
                    {
                        "action": "captcha_on_sensitive",
                        "description": "Add CAPTCHA to sensitive data endpoints",
                        "impact_on_legitimate": "medium",
                        "effectiveness": "high",
                        "implementation_effort": "low"
                    }
                ],
                Layer7AttackType.SLOW_REQUEST: [
                    {
                        "action": "connection_timeout",
                        "description": "Configure strict connection timeouts",
                        "impact_on_legitimate": "low",
                        "effectiveness": "high",
                        "implementation_effort": "low"
                    },
                    {
                        "action": "request_size_limit",
                        "description": "Limit request body size",
                        "impact_on_legitimate": "low",
                        "effectiveness": "medium",
                        "implementation_effort": "low"
                    }
                ]
            }
            
            for rec in base_recs.get(attack_type, []):
                rec["attack_type"] = attack_type.value
                rec["priority"] = count
                recommendations.append(rec)
        
        # Sort by effectiveness and impact
        effectiveness_order = {"high": 3, "medium": 2, "low": 1}
        impact_order = {"positive": 4, "low": 3, "medium": 2, "high": 1}
        
        recommendations.sort(
            key=lambda x: (
                effectiveness_order.get(x["effectiveness"], 0),
                impact_order.get(x["impact_on_legitimate"], 0),
                x["priority"]
            ),
            reverse=True
        )
        
        return recommendations[:5]  # Top 5 recommendations


# =============================================================================
# STIX 2.1 ALIGNMENT - Threat Intelligence Sharing
# =============================================================================

class STIXMapper:
    """
    Maps Layer 7 DDoS detection results to STIX 2.1 format
    for threat intelligence sharing.
    """
    
    @staticmethod
    def anomaly_to_stix(anomaly: Anomaly) -> Dict:
        """
        Convert an anomaly to STIX 2.1 Indicator format.
        """
        stix_indicator = {
            "type": "indicator",
            "spec_version": "2.1",
            "id": f"indicator--{anomaly.anomaly_id}",
            "created": anomaly.timestamp.isoformat(),
            "modified": anomaly.timestamp.isoformat(),
            "name": f"Layer 7 DDoS: {anomaly.anomaly_type}",
            "description": anomaly.explanation,
            "indicator_types": ["malicious-activity"],
            "pattern_type": "stix",
            "pattern": STIXMapper._generate_stix_pattern(anomaly),
            "valid_from": anomaly.timestamp.isoformat(),
            "confidence": int(anomaly.confidence * 100),
            "severity": anomaly.severity,
            "labels": [
                "ddos",
                "layer-7",
                anomaly.attack_type.value if anomaly.attack_type else "unknown"
            ],
            "external_references": [
                {
                    "source_name": "knowledge-graph-ddos",
                    "external_id": anomaly.anomaly_id
                }
            ]
        }
        
        return stix_indicator
    
    @staticmethod
    def _generate_stix_pattern(anomaly: Anomaly) -> str:
        """Generate STIX pattern from anomaly evidence."""
        patterns = []
        
        for evidence in anomaly.evidence:
            if "IP address" in evidence:
                # Extract IP from evidence
                parts = evidence.split(": ")
                if len(parts) > 1:
                    ip = parts[1].strip()
                    patterns.append(f"[ipv4-addr:value = '{ip}']")
            
            if "Session" in evidence or "session" in evidence:
                parts = evidence.split(": ")
                if len(parts) > 1:
                    session = parts[1].strip()
                    patterns.append(f"[x-session-id:value = '{session}']")
        
        if anomaly.target_endpoint:
            patterns.append(f"[url:value = '{anomaly.target_endpoint}']")
        
        if patterns:
            return " AND ".join(patterns)
        return "[unknown:value = 'true']"
    
    @staticmethod
    def attack_to_stix_attack_pattern(attack_type: Layer7AttackType) -> Dict:
        """
        Map Layer 7 attack type to STIX Attack Pattern.
        """
        mitre_mapping = {
            Layer7AttackType.HTTP_FLOOD: "T1498.001",  # Application Layer DoS
            Layer7AttackType.LOGIN_FLOOD: "T1110.003",  # Brute Force
            Layer7AttackType.SLOW_REQUEST: "T1498.001",  # Application Layer DoS
            Layer7AttackType.API_ABUSE: "T1190",  # Exploit Public-Facing Application
            Layer7AttackType.SCRAPING: "T1213",  # Data from Information Repositories
        }
        
        return {
            "type": "attack-pattern",
            "spec_version": "2.1",
            "id": f"attack-pattern--{attack_type.value.lower()}",
            "name": attack_type.value,
            "description": STIXMapper._get_attack_description(attack_type),
            "external_references": [
                {
                    "source_name": "mitre-attack",
                    "external_id": mitre_mapping.get(attack_type, "T1498")
                }
            ] if attack_type in mitre_mapping else [],
            "kill_chain_phases": [
                {
                    "kill_chain_name": "mitre-attack",
                    "phase_name": "impact"
                }
            ]
        }
    
    @staticmethod
    def _get_attack_description(attack_type: Layer7AttackType) -> str:
        descriptions = {
            Layer7AttackType.HTTP_FLOOD: "HTTP flood attack targeting web application endpoints with high request volume",
            Layer7AttackType.LOGIN_FLOOD: "Brute force or credential stuffing attack against authentication endpoints",
            Layer7AttackType.SLOW_REQUEST: "Slow request attack (Slowloris/RUDY) consuming server connections",
            Layer7AttackType.API_ABUSE: "Abuse of API endpoints through excessive requests or manipulation",
            Layer7AttackType.SCRAPING: "Automated scraping of web application content",
            Layer7AttackType.BOT_ATTACK: "Automated bot traffic exhibiting malicious patterns"
        }
        return descriptions.get(attack_type, "Layer 7 DDoS attack")
    
    @staticmethod
    def export_stix_bundle(anomalies: List[Anomaly]) -> Dict:
        """
        Export all anomalies as a STIX 2.1 bundle.
        """
        objects = []
        
        for anomaly in anomalies:
            objects.append(STIXMapper.anomaly_to_stix(anomaly))
            
            if anomaly.attack_type:
                attack_pattern = STIXMapper.attack_to_stix_attack_pattern(anomaly.attack_type)
                if attack_pattern not in objects:
                    objects.append(attack_pattern)
        
        return {
            "type": "bundle",
            "id": "bundle--layer7-ddos-detection",
            "objects": objects
        }


# =============================================================================
# GRAPH VISUALIZATION EXPORT
# =============================================================================

class GraphExporter:
    """
    Export knowledge graph in various visualization formats.
    """
    
    @staticmethod
    def to_graphml(kg: Layer7KnowledgeGraph, filepath: str) -> None:
        """Export to GraphML format for tools like Gephi, Cytoscape."""
        # Create a clean graph for export
        export_graph = nx.MultiDiGraph()
        
        for node_id, node_data in kg.graph.nodes(data=True):
            # Flatten properties for GraphML
            clean_data = {k: str(v) if not isinstance(v, (str, int, float, bool)) else v 
                         for k, v in node_data.items()}
            export_graph.add_node(node_id, **clean_data)
        
        for u, v, key, data in kg.graph.edges(data=True, keys=True):
            clean_data = {k: str(v) if not isinstance(v, (str, int, float, bool)) else v 
                         for k, v in data.items()}
            export_graph.add_edge(u, v, key=key, **clean_data)
        
        nx.write_graphml(export_graph, filepath)
    
    @staticmethod
    def to_gexf(kg: Layer7KnowledgeGraph, filepath: str) -> None:
        """Export to GEXF format for Gephi."""
        nx.write_gexf(kg.graph, filepath)
    
    @staticmethod
    def to_cytoscape_js(kg: Layer7KnowledgeGraph) -> Dict:
        """Export to Cytoscape.js format for web visualization."""
        elements = {"nodes": [], "edges": []}
        
        # Color mapping for entity types
        color_map = {
            "HTTPRequest": "#4CAF50",
            "Endpoint": "#2196F3",
            "ApplicationSession": "#FF9800",
            "Anomaly": "#F44336",
            "IPAddress": "#9C27B0",
            "Behavior": "#00BCD4"
        }
        
        for node_id, node_data in kg.graph.nodes(data=True):
            entity_type = node_data.get("type", "Unknown")
            elements["nodes"].append({
                "data": {
                    "id": node_id,
                    "label": node_id[:30],
                    "type": entity_type,
                    "color": color_map.get(entity_type, "#607D8B"),
                    **{k: str(v)[:100] for k, v in node_data.items() if k != "type"}
                }
            })
        
        edge_id = 0
        for u, v, key, data in kg.graph.edges(data=True, keys=True):
            elements["edges"].append({
                "data": {
                    "id": f"edge_{edge_id}",
                    "source": u,
                    "target": v,
                    "label": key,
                    **{k: str(v)[:50] for k, v in data.items() if k != "type"}
                }
            })
            edge_id += 1
        
        return elements
    
    @staticmethod
    def to_mermaid(kg: Layer7KnowledgeGraph, max_nodes: int = 50) -> str:
        """Export to Mermaid diagram format."""
        lines = ["graph TD"]
        
        # Limit nodes for readability
        nodes = list(kg.graph.nodes(data=True))[:max_nodes]
        node_ids = {n[0] for n in nodes}
        
        # Add nodes
        for node_id, node_data in nodes:
            entity_type = node_data.get("type", "Unknown")
            label = node_id.replace("_", " ")[:20]
            lines.append(f"    {node_id[:15]}[\"{label}<br/>({entity_type})\"]")
        
        # Add edges
        for u, v, key, data in kg.graph.edges(data=True, keys=True):
            if u in node_ids and v in node_ids:
                lines.append(f"    {u[:15]} -->|{key}| {v[:15]}")
        
        return "\n".join(lines)


# =============================================================================
# ANOMALY CORRELATION ENGINE - Coordinated Attack Detection
# =============================================================================

class AnomalyCorrelationEngine:
    """
    Correlates multiple anomalies to detect coordinated attacks.
    """
    
    def __init__(self, kg: Layer7KnowledgeGraph):
        self.kg = kg
    
    def detect_coordinated_attacks(self) -> List[Dict]:
        """
        Detect if multiple anomalies are part of a coordinated attack.
        
        Correlation criteria:
        - Same target endpoint
        - Temporal proximity
        - Related sessions
        - Similar attack patterns
        """
        coordinated_attacks = []
        anomalies = self.kg.anomalies
        
        if len(anomalies) < 2:
            return coordinated_attacks
        
        # Group by endpoint
        by_endpoint = defaultdict(list)
        for anomaly in anomalies:
            if anomaly.target_endpoint:
                by_endpoint[anomaly.target_endpoint].append(anomaly)
        
        # Analyze each endpoint for coordinated patterns
        for endpoint, endpoint_anomalies in by_endpoint.items():
            if len(endpoint_anomalies) < 2:
                continue
            
            # Check temporal correlation
            timestamps = [a.timestamp for a in endpoint_anomalies]
            if timestamps:
                time_span = (max(timestamps) - min(timestamps)).total_seconds()
                
                # If anomalies occur within 5 minutes, likely coordinated
                if time_span < 300:
                    # Check session overlap
                    all_sessions = set()
                    for a in endpoint_anomalies:
                        all_sessions.update(a.related_sessions)
                    
                    # Check attack type diversity
                    attack_types = set(
                        a.attack_type for a in endpoint_anomalies if a.attack_type
                    )
                    
                    coordinated_attacks.append({
                        "type": "coordinated_attack",
                        "endpoint": endpoint,
                        "anomaly_count": len(endpoint_anomalies),
                        "time_span_seconds": time_span,
                        "unique_sessions": len(all_sessions),
                        "attack_types": [at.value for at in attack_types],
                        "confidence": min(1.0, len(endpoint_anomalies) * 0.2),
                        "severity": "critical" if len(endpoint_anomalies) > 5 else "high",
                        "description": f"Coordinated attack on {endpoint} with {len(endpoint_anomalies)} anomalies in {time_span:.0f}s"
                    })
        
        # Cross-endpoint correlation (multi-vector attacks)
        if len(by_endpoint) > 1:
            all_timestamps = [a.timestamp for a in anomalies]
            if all_timestamps:
                total_time_span = (max(all_timestamps) - min(all_timestamps)).total_seconds()
                
                if total_time_span < 600:  # 10 minutes
                    coordinated_attacks.append({
                        "type": "multi_vector_attack",
                        "endpoints": list(by_endpoint.keys()),
                        "total_anomalies": len(anomalies),
                        "time_span_seconds": total_time_span,
                        "confidence": min(1.0, len(anomalies) * 0.1),
                        "severity": "critical",
                        "description": f"Multi-vector attack across {len(by_endpoint)} endpoints"
                    })
        
        return coordinated_attacks
    
    def calculate_attack_graph(self) -> Dict:
        """
        Build a graph of related anomalies for visualization.
        """
        attack_graph = nx.Graph()
        
        for i, anomaly in enumerate(self.kg.anomalies):
            attack_graph.add_node(
                f"anomaly_{i}",
                type=anomaly.anomaly_type,
                attack_type=anomaly.attack_type.value if anomaly.attack_type else None,
                severity=anomaly.severity,
                score=anomaly.score
            )
        
        # Connect anomalies with shared characteristics
        for i, a1 in enumerate(self.kg.anomalies):
            for j, a2 in enumerate(self.kg.anomalies[i+1:], i+1):
                # Same endpoint
                if a1.target_endpoint and a1.target_endpoint == a2.target_endpoint:
                    attack_graph.add_edge(f"anomaly_{i}", f"anomaly_{j}", relation="same_endpoint")
                
                # Shared sessions
                shared_sessions = set(a1.related_sessions) & set(a2.related_sessions)
                if shared_sessions:
                    attack_graph.add_edge(f"anomaly_{i}", f"anomaly_{j}", relation="shared_session")
                
                # Same attack type
                if a1.attack_type and a1.attack_type == a2.attack_type:
                    attack_graph.add_edge(f"anomaly_{i}", f"anomaly_{j}", relation="same_attack_type")
        
        return {
            "nodes": [
                {"id": n, **d} for n, d in attack_graph.nodes(data=True)
            ],
            "edges": [
                {"source": u, "target": v, "relation": d.get("relation", "unknown")}
                for u, v, d in attack_graph.edges(data=True)
            ],
            "connected_components": nx.number_connected_components(attack_graph)
        }


# =============================================================================
# REAL-TIME DETECTION PIPELINE
# =============================================================================

class RealTimeDetectionPipeline:
    """
    Real-time Layer 7 DDoS detection pipeline.
    
    Processes HTTP requests in real-time and triggers alerts.
    """
    
    def __init__(self, kg: Layer7KnowledgeGraph, alert_callback=None):
        self.kg = kg
        self.detector = Layer7AnomalyDetector(kg)
        self.query_engine = SemanticQueryEngine(kg)
        self.correlation_engine = AnomalyCorrelationEngine(kg)
        self.alert_callback = alert_callback
        
        # Sliding window for detection
        self.window_size = timedelta(minutes=5)
        self.last_detection = datetime.now() - timedelta(minutes=10)
        
        # Alert deduplication
        self.recent_alerts = {}
        self.alert_cooldown = timedelta(minutes=1)
    
    def process_request(self, request: HTTPRequest) -> Optional[Dict]:
        """
        Process a single HTTP request in real-time.
        
        Returns alert if anomaly detected.
        """
        # Add to knowledge graph
        self.kg.add_http_request(request)
        
        # Check if we should run detection
        now = datetime.now()
        if now - self.last_detection < timedelta(seconds=10):
            return None  # Don't run detection too frequently
        
        self.last_detection = now
        
        # Run detection
        anomalies = self.detector.detect(self.window_size)
        
        if anomalies:
            # Check for coordinated attacks
            coordinated = self.correlation_engine.detect_coordinated_attacks()
            
            # Generate alerts
            alerts = []
            for anomaly in anomalies:
                alert_key = f"{anomaly.anomaly_type}_{anomaly.target_endpoint}"
                
                # Deduplicate alerts
                if alert_key in self.recent_alerts:
                    last_alert_time = self.recent_alerts[alert_key]
                    if now - last_alert_time < self.alert_cooldown:
                        continue
                
                self.recent_alerts[alert_key] = now
                
                alert = {
                    "timestamp": now.isoformat(),
                    "anomaly_type": anomaly.anomaly_type,
                    "attack_type": anomaly.attack_type.value if anomaly.attack_type else None,
                    "severity": anomaly.severity,
                    "score": anomaly.score,
                    "endpoint": anomaly.target_endpoint,
                    "explanation": anomaly.explanation,
                    "evidence": anomaly.evidence
                }
                alerts.append(alert)
                
                if self.alert_callback:
                    self.alert_callback(alert)
            
            if alerts or coordinated:
                return {
                    "alerts": alerts,
                    "coordinated_attacks": coordinated,
                    "endpoint_status": self.query_engine.query_endpoint_under_attack()
                }
        
        return None
    
    def get_current_status(self) -> Dict:
        """Get current detection status."""
        return {
            "total_requests": self.kg.graph.number_of_nodes(),
            "total_anomalies": len(self.kg.anomalies),
            "active_sessions": len(self.kg.sessions),
            "monitored_endpoints": len(self.kg.endpoints),
            "endpoint_under_attack": self.query_engine.query_endpoint_under_attack(),
            "attack_graph": self.correlation_engine.calculate_attack_graph()
        }


# =============================================================================
# ENHANCED SIMULATION WITH NEW FEATURES
# =============================================================================

def simulate_layer7_attack_enhanced():
    """
    Enhanced simulation demonstrating all new features.
    """
    print("=" * 70)
    print("Knowledge Graph-Based Layer 7 DDoS Detection - Enhanced Simulation")
    print("=" * 70)
    
    # Initialize knowledge graph
    kg = Layer7KnowledgeGraph()
    
    # Register endpoints
    print("\n[1] Registering application endpoints...")
    endpoints = [
        Endpoint("/login", computational_cost=0.8, is_cacheable=False, requires_auth=False, depends_on_db=True, criticality="high"),
        Endpoint("/api/products", computational_cost=0.6, is_cacheable=True, requires_auth=False, depends_on_db=True, criticality="medium"),
        Endpoint("/api/search", computational_cost=0.9, is_cacheable=False, requires_auth=False, depends_on_db=True, criticality="high"),
        Endpoint("/checkout", computational_cost=0.95, is_cacheable=False, requires_auth=True, depends_on_db=True, criticality="critical"),
        Endpoint("/api/graphql", computational_cost=0.85, is_cacheable=False, requires_auth=True, depends_on_db=True, criticality="high"),
    ]
    
    for endpoint in endpoints:
        kg.register_endpoint(endpoint)
        print(f"   Registered: {endpoint.path} (cost: {endpoint.computational_cost})")
    
    # Simulate normal traffic
    print("\n[2] Adding normal traffic...")
    normal_requests = [
        HTTPRequest(
            request_id=f"normal_{i}",
            method="GET",
            path=f"/api/products/{i % 10}",
            endpoint="/api/products",
            src_ip=f"192.168.1.{i % 50}",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            session_id=f"session_{i % 20}",
            response_code=200,
            response_time_ms=50 + (i % 30),
            timestamp=datetime.now() - timedelta(seconds=i)
        )
        for i in range(100)
    ]
    
    for request in normal_requests:
        kg.add_http_request(request)
    
    print(f"   Added {len(normal_requests)} normal requests")
    
    # Simulate multi-vector Layer 7 attack
    print("\n[3] Simulating multi-vector Layer 7 DDoS attack...")
    
    # HTTP Flood on search endpoint
    http_flood = [
        HTTPRequest(
            request_id=f"http_flood_{i}",
            method="GET",
            path="/api/search?q=attack",
            endpoint="/api/search",
            src_ip=f"203.0.113.{i % 255}",
            user_agent="python-requests/2.28.0",
            session_id=f"attack_session_{i % 10}",
            response_code=200,
            response_time_ms=200 + (i % 50),
            timestamp=datetime.now()
        )
        for i in range(500)
    ]
    
    # Login flood
    login_flood = [
        HTTPRequest(
            request_id=f"login_flood_{i}",
            method="POST",
            path="/login",
            endpoint="/login",
            src_ip=f"198.51.100.{i % 100}",
            user_agent="curl/7.68.0",
            session_id="login_attack_session",
            response_code=401,
            response_time_ms=100,
            timestamp=datetime.now()
        )
        for i in range(50)
    ]
    
    # API abuse
    api_abuse = [
        HTTPRequest(
            request_id=f"api_abuse_{i}",
            method="POST",
            path="/api/graphql",
            endpoint="/api/graphql",
            src_ip=f"10.0.0.{i % 50}",
            user_agent="PostmanRuntime/7.29.0",
            session_id=f"api_abuse_session_{i % 5}",
            response_code=400 if i % 3 == 0 else 200,
            response_time_ms=150,
            timestamp=datetime.now()
        )
        for i in range(200)
    ]
    
    # Update sessions with attack metadata
    if "login_attack_session" in kg.sessions:
        kg.sessions["login_attack_session"].failed_logins = 50
        kg.sessions["login_attack_session"].login_attempts = 50
    
    # Add bot behavior profiles
    for i in range(10):
        profile = BehaviorProfile(
            profile_id=f"attack_profile_{i}",
            session_id=f"attack_session_{i}",
            header_variability=0.05,
            fingerprint_variability=0.02,
            navigation_diversity=0.1,
            request_interval_avg_ms=100,
            request_interval_std=5,
            is_bot_like=True,
            pattern_type="malicious"
        )
        kg.update_behavior_profile(profile)
    
    # Add all attack requests
    for request in http_flood + login_flood + api_abuse:
        kg.add_http_request(request)
    
    print(f"   Added {len(http_flood) + len(login_flood) + len(api_abuse)} attack requests")
    
    # Run detection
    print("\n[4] Running Layer 7 anomaly detection...")
    detector = Layer7AnomalyDetector(kg)
    anomalies = detector.detect()
    
    print(f"   Detected {len(anomalies)} anomalies")
    
    # Semantic queries
    print("\n[5] Semantic Query Results:")
    query_engine = SemanticQueryEngine(kg)
    
    print("\n   Query: 'Which endpoint is under attack?'")
    attack_status = query_engine.query_endpoint_under_attack()
    print(f"   Result: {attack_status['endpoint']}")
    print(f"   Anomaly count: {attack_status['anomaly_count']}")
    print(f"   Confidence: {attack_status['confidence']:.0%}")
    
    print("\n   Query: 'What signals support HTTP Flood hypothesis?'")
    evidence = query_engine.query_attack_hypothesis_evidence(Layer7AttackType.HTTP_FLOOD)
    print(f"   Evidence count: {evidence['evidence_count']}")
    print(f"   Evidence by type: {list(evidence['evidence_by_type'].keys())}")
    
    print("\n   Query: 'Best mitigation for /api/search?'")
    mitigation = query_engine.query_best_mitigation("/api/search")
    print(f"   Top recommendation: {mitigation['recommendations'][0]['action'] if mitigation['recommendations'] else 'None'}")
    
    # Coordinated attack detection
    print("\n[6] Coordinated Attack Detection:")
    correlation_engine = AnomalyCorrelationEngine(kg)
    coordinated = correlation_engine.detect_coordinated_attacks()
    
    for attack in coordinated:
        print(f"   - {attack['type']}: {attack['description']}")
    
    # STIX export
    print("\n[7] STIX 2.1 Export:")
    stix_bundle = STIXMapper.export_stix_bundle(anomalies[:5])
    print(f"   Exported {len(stix_bundle['objects'])} STIX objects")
    
    # Graph export
    print("\n[8] Graph Export:")
    GraphExporter.to_graphml(kg, "layer7_ddos_graph.graphml")
    GraphExporter.to_gexf(kg, "layer7_ddos_graph.gexf")
    print("   Exported: layer7_ddos_graph.graphml")
    print("   Exported: layer7_ddos_graph.gexf")
    
    cytoscape = GraphExporter.to_cytoscape_js(kg)
    print(f"   Cytoscape.js: {len(cytoscape['nodes'])} nodes, {len(cytoscape['edges'])} edges")
    
    # Explainability
    print("\n[9] Top Anomaly Explanations:")
    sorted_anomalies = sorted(anomalies, key=lambda x: x.score, reverse=True)[:3]
    
    for anomaly in sorted_anomalies:
        print(f"\n   {'='*50}")
        print(ExplainabilityEngine.generate_explanation(anomaly))
    
    # Real-time pipeline demo
    print("\n[10] Real-Time Pipeline Demo:")
    pipeline = RealTimeDetectionPipeline(kg, alert_callback=lambda a: print(f"   ALERT: {a['attack_type']} on {a['endpoint']}"))
    
    # Simulate real-time request
    test_request = HTTPRequest(
        request_id="realtime_test",
        method="GET",
        path="/api/search?q=exploit",
        endpoint="/api/search",
        src_ip="203.0.113.100",
        user_agent="python-requests/2.28.0",
        session_id="attack_session_0",
        response_code=200,
        response_time_ms=500,
        timestamp=datetime.now()
    )
    
    result = pipeline.process_request(test_request)
    if result:
        print(f"   Detection triggered: {len(result.get('alerts', []))} alerts")
    
    print("\n" + "=" * 70)
    print("Simulation Complete")
    print("=" * 70)
    
    return kg, anomalies


def simulate_dns_layer7_attack():
    """
    Simulate DNS Layer 7 DDoS attack scenarios for demonstration.
    
    This simulation demonstrates detection of various DNS-based Layer 7 attacks:
    - QName Randomization (Random Subdomain Attack)
    - NXDOMAIN Flood
    - DNS Water Torture
    - DNS Amplification
    - DNS Tunneling
    - Phantom Domain Attack
    """
    print("=" * 70)
    print("Knowledge Graph-Based DNS Layer 7 DDoS Detection Simulation")
    print("=" * 70)
    
    # Initialize knowledge graph
    kg = Layer7KnowledgeGraph()
    
    # Register DNS domains being monitored
    print("\n[1] Registering monitored DNS domains...")
    domains = [
        DNSDomain(domain="example.com", is_authoritative=True, is_internal=False, expected_query_rate=50.0),
        DNSDomain(domain="api.example.com", is_authoritative=True, is_internal=True, expected_query_rate=100.0),
        DNSDomain(domain="cdn.example.com", is_authoritative=True, is_internal=True, expected_query_rate=500.0),
        DNSDomain(domain="internal.corp", is_authoritative=True, is_internal=True, expected_query_rate=20.0),
    ]
    
    for domain in domains:
        kg.register_dns_domain(domain)
        print(f"   Registered: {domain.domain} (expected QPS: {domain.expected_query_rate})")
    
    # Simulate normal DNS traffic
    print("\n[2] Adding normal DNS traffic...")
    normal_queries = []
    base_time = datetime.now() - timedelta(minutes=30)
    
    normal_domains = [
        ("www.example.com", "A"),
        ("api.example.com", "A"),
        ("mail.example.com", "MX"),
        ("cdn.example.com", "A"),
        ("www.example.com", "AAAA"),
    ]
    
    for i in range(200):
        qname, qtype = normal_domains[i % len(normal_domains)]
        query = DNSQuery(
            query_id=f"normal_dns_{i}",
            qname=qname,
            qtype=qtype,
            src_ip=f"192.168.1.{i % 50}",
            dst_ip="10.0.0.1",  # DNS resolver
            response_code="NOERROR",
            response_time_ms=10 + (i % 20),
            timestamp=base_time + timedelta(seconds=i * 2),
            answer_count=1,
            is_response_cached=i % 3 == 0,
            query_size=30 + (i % 10),
            response_size=60 + (i % 30),
            edns_enabled=i % 2 == 0,
            dnssec_ok=i % 5 == 0
        )
        normal_queries.append(query)
        kg.add_dns_query(query)
    
    print(f"   Added {len(normal_queries)} normal DNS queries")
    print(f"   Graph nodes: {kg.graph.number_of_nodes()}")
    print(f"   Graph edges: {kg.graph.number_of_edges()}")
    
    # Simulate DNS Layer 7 attacks
    print("\n[3] Simulating DNS Layer 7 DDoS attacks...")
    
    # Attack 1: QName Randomization (Random Subdomain Attack)
    print("\n   [3.1] QName Randomization Attack (Random Subdomain)...")
    import random
    import string
    
    def random_string(length=12):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    qname_randomization_queries = []
    for i in range(300):
        # Generate random subdomain
        random_subdomain = random_string(15)
        qname = f"{random_subdomain}.example.com"
        
        query = DNSQuery(
            query_id=f"qname_rand_{i}",
            qname=qname,
            qtype="A",
            src_ip=f"203.0.113.{i % 100}",  # Attacker IPs
            dst_ip="10.0.0.1",
            response_code="NXDOMAIN",  # Most will be NXDOMAIN
            response_time_ms=50 + (i % 30),
            timestamp=datetime.now() - timedelta(seconds=300 - i),
            answer_count=0,
            is_response_cached=False,
            query_size=50 + len(random_subdomain),
            response_size=100,
            edns_enabled=True,
            dnssec_ok=False
        )
        qname_randomization_queries.append(query)
        kg.add_dns_query(query)
    
    print(f"      Added {len(qname_randomization_queries)} random subdomain queries")
    
    # Attack 2: NXDOMAIN Flood
    print("\n   [3.2] NXDOMAIN Flood Attack...")
    nxdomain_flood_queries = []
    nonexistent_domains = [
        f"nonexistent{i}.example.com" for i in range(100)
    ]
    
    for i in range(500):
        query = DNSQuery(
            query_id=f"nxdomain_flood_{i}",
            qname=nonexistent_domains[i % 100],
            qtype="A",
            src_ip=f"198.51.100.{i % 50}",
            dst_ip="10.0.0.1",
            response_code="NXDOMAIN",
            response_time_ms=30 + (i % 20),
            timestamp=datetime.now() - timedelta(seconds=200 - i),
            answer_count=0,
            is_response_cached=False,
            query_size=35,
            response_size=80,
            edns_enabled=True,
            dnssec_ok=False
        )
        nxdomain_flood_queries.append(query)
        kg.add_dns_query(query)
    
    print(f"      Added {len(nxdomain_flood_queries)} NXDOMAIN flood queries")
    
    # Attack 3: DNS Water Torture (Slow-drip attack)
    print("\n   [3.3] DNS Water Torture Attack (Slow-drip)...")
    water_torture_queries = []
    
    # Steady stream of unique subdomains over extended period
    for i in range(150):
        subdomain = f"slow{i:04d}.api.example.com"
        
        query = DNSQuery(
            query_id=f"water_torture_{i}",
            qname=subdomain,
            qtype="A",
            src_ip=f"10.0.0.{100 + (i % 20)}",  # Distributed source IPs
            dst_ip="10.0.0.1",
            response_code="NOERROR" if i % 5 == 0 else "NXDOMAIN",
            response_time_ms=100 + (i % 50),
            timestamp=datetime.now() - timedelta(minutes=60 - i * 0.4),  # Spread over 1 hour
            answer_count=1 if i % 5 == 0 else 0,
            is_response_cached=False,
            query_size=40,
            response_size=60 if i % 5 == 0 else 80,
            edns_enabled=True,
            dnssec_ok=False
        )
        water_torture_queries.append(query)
        kg.add_dns_query(query)
    
    print(f"      Added {len(water_torture_queries)} water torture queries (slow-drip)")
    
    # Attack 4: DNS Amplification
    print("\n   [3.4] DNS Amplification Attack...")
    amplification_queries = []
    
    for i in range(100):
        query = DNSQuery(
            query_id=f"dns_amp_{i}",
            qname="example.com",
            qtype="ANY",  # ANY queries produce large responses
            src_ip=f"1.2.3.{i % 255}",  # Spoofed victim IPs
            dst_ip="10.0.0.1",
            response_code="NOERROR",
            response_time_ms=20,
            timestamp=datetime.now() - timedelta(seconds=100 - i),
            answer_count=10,
            is_response_cached=False,
            query_size=30,  # Small query
            response_size=4000,  # Large response (amplification)
            edns_enabled=True,
            dnssec_ok=True
        )
        amplification_queries.append(query)
        kg.add_dns_query(query)
    
    print(f"      Added {len(amplification_queries)} amplification queries")
    print(f"      Amplification factor: ~133x (4000/30 bytes)")
    
    # Attack 5: DNS Tunneling (Data exfiltration simulation)
    print("\n   [3.5] DNS Tunneling Attack...")
    tunneling_queries = []
    
    # Simulate encoded data in subdomain (base64-like patterns)
    encoded_data = [
        "Y2F0YXN0cm9waGU",  # base64-like encoded data
        "ZGF0YWV4ZmlsdHJh",
        "Y29tbWFuZGVjb250cm9s",
        "ZXhmaWx0cmF0ZWRhdGE",
        "c2VjcmV0a2V5MTIz",
    ]
    
    for i in range(80):
        data = encoded_data[i % len(encoded_data)]
        # Long subdomain with encoded data
        qname = f"{data}{i:03d}.tunnel.example.com"
        
        query = DNSQuery(
            query_id=f"dns_tunnel_{i}",
            qname=qname,
            qtype="TXT",  # TXT records commonly used for tunneling
            src_ip="10.0.0.50",
            dst_ip="10.0.0.1",
            response_code="NOERROR",
            response_time_ms=150,  # Slightly slower (tunneling overhead)
            timestamp=datetime.now() - timedelta(seconds=80 - i),
            answer_count=1,
            is_response_cached=False,
            query_size=80 + len(data),  # Long queries
            response_size=200,
            edns_enabled=True,
            dnssec_ok=False
        )
        tunneling_queries.append(query)
        kg.add_dns_query(query)
    
    print(f"      Added {len(tunneling_queries)} tunneling queries")
    
    # Attack 6: Phantom Domain Attack
    print("\n   [3.6] Phantom Domain Attack...")
    phantom_queries = []
    
    # Queries to domains with slow/non-responsive authoritative servers
    phantom_domains = [
        "slow-phanton.example.com",
        "timeout-phantom.example.com",
        "delayed-phantom.example.com",
    ]
    
    for i in range(60):
        query = DNSQuery(
            query_id=f"phantom_{i}",
            qname=phantom_domains[i % len(phantom_domains)],
            qtype="A",
            src_ip=f"172.16.0.{i % 30}",
            dst_ip="10.0.0.1",
            response_code="SERVFAIL" if i % 3 == 0 else "NOERROR",
            response_time_ms=5000 + (i % 3000),  # Very slow responses
            timestamp=datetime.now() - timedelta(seconds=50 - i),
            answer_count=0 if i % 3 == 0 else 1,
            is_response_cached=False,
            query_size=40,
            response_size=80,
            edns_enabled=True,
            dnssec_ok=False
        )
        phantom_queries.append(query)
        kg.add_dns_query(query)
    
    print(f"      Added {len(phantom_queries)} phantom domain queries")
    
    print(f"\n   Total attack queries: {len(qname_randomization_queries) + len(nxdomain_flood_queries) + len(water_torture_queries) + len(amplification_queries) + len(tunneling_queries) + len(phantom_queries)}")
    print(f"   Graph nodes: {kg.graph.number_of_nodes()}")
    print(f"   Graph edges: {kg.graph.number_of_edges()}")
    
    # Run DNS anomaly detection
    print("\n[4] Running DNS Layer 7 anomaly detection...")
    detector = Layer7AnomalyDetector(kg)
    anomalies = detector.detect()
    
    print(f"\n[5] Detection Results:")
    print(f"   Total anomalies detected: {len(anomalies)}")
    
    # Group by attack type
    attack_counts = defaultdict(int)
    for anomaly in anomalies:
        if anomaly.attack_type:
            attack_counts[anomaly.attack_type.value] += 1
    
    print("\n   DNS Attack Type Distribution:")
    dns_attack_types = [
        "QNameRandomization", "NXDOMAINFlood", "DNSWaterTorture",
        "DNSAmplification", "DNSTunneling", "PhantomDomainAttack"
    ]
    for attack_type in dns_attack_types:
        count = attack_counts.get(attack_type, 0)
        if count > 0:
            print(f"   - {attack_type}: {count} anomalies")
    
    # Display top DNS anomalies with explanations
    print("\n   Top DNS Anomalies (by score):")
    dns_anomalies = [a for a in anomalies if a.attack_type and a.attack_type.value in dns_attack_types]
    sorted_anomalies = sorted(dns_anomalies, key=lambda x: x.score, reverse=True)[:5]
    
    for anomaly in sorted_anomalies:
        print(f"\n   {'='*50}")
        print(ExplainabilityEngine.generate_explanation(anomaly))
    
    # DNS Domain metrics
    print("\n[6] DNS Domain Metrics:")
    domain_metrics = kg.calculate_domain_metrics()
    for domain, metrics in domain_metrics.items():
        print(f"   {domain}:")
        print(f"      Queries: {metrics['query_count']}, QPS: {metrics['queries_per_second']:.2f}")
        print(f"      Unique subdomains: {metrics['unique_subdomains']}")
        print(f"      NXDOMAIN ratio: {metrics['nxdomain_ratio']:.2%}")
        print(f"      Unique source IPs: {metrics['unique_src_ips']}")
    
    # Mitigation recommendations
    print("\n[7] Mitigation Recommendations by Attack Type:")
    for anomaly in sorted_anomalies[:3]:
        recommendations = ExplainabilityEngine.get_mitigation_recommendations(anomaly)
        print(f"\n   For {anomaly.attack_type.value if anomaly.attack_type else 'Unknown'}:")
        for rec in recommendations[:3]:
            print(f"      - {rec}")
    
    # Export DNS attack graph
    print("\n[8] Exporting DNS attack knowledge graph...")
    export_data = {
        "nodes": [e.to_dict() for e in kg.entities.values()],
        "edges": [r.to_dict() for r in kg.relations],
        "anomalies": [a.to_entity().properties for a in kg.anomalies],
        "dns_stats": {
            "total_queries": len(kg.dns_queries),
            "total_domains": len(kg.dns_domains),
            "attack_queries": len(qname_randomization_queries) + len(nxdomain_flood_queries) + 
                            len(water_torture_queries) + len(amplification_queries) + 
                            len(tunneling_queries) + len(phantom_queries)
        }
    }
    
    with open("dns_layer7_knowledge_graph_export.json", "w") as f:
        json.dump(export_data, f, indent=2, default=str)
    
    print("   Exported to: dns_layer7_knowledge_graph_export.json")
    
    # STIX export for DNS attacks
    print("\n[9] STIX 2.1 Export for DNS Attacks:")
    stix_bundle = STIXMapper.export_stix_bundle(sorted_anomalies)
    print(f"   Exported {len(stix_bundle['objects'])} STIX objects")
    
    # Graph export
    print("\n[10] Graph Export:")
    GraphExporter.to_graphml(kg, "dns_layer7_ddos_graph.graphml")
    GraphExporter.to_gexf(kg, "dns_layer7_ddos_graph.gexf")
    print("   Exported: dns_layer7_ddos_graph.graphml")
    print("   Exported: dns_layer7_ddos_graph.gexf")
    
    print("\n" + "=" * 70)
    print("DNS Layer 7 DDoS Detection Simulation Complete")
    print("=" * 70)
    
    return kg, anomalies


if __name__ == "__main__":
    print("Knowledge Graph-Based Layer 7 DDoS Detection System")
    print("=" * 70)
    print("\nAvailable simulations:")
    print("  1. HTTP/Application Layer 7 DDoS Attack Simulation")
    print("  2. DNS Layer 7 DDoS Attack Simulation")
    print("\nRunning both simulations...\n")
    
    print("\n" + "#" * 70)
    print("# SIMULATION 1: HTTP/Application Layer 7 DDoS")
    print("#" * 70 + "\n")
    kg_http, anomalies_http = simulate_layer7_attack_enhanced()
    
    print("\n\n" + "#" * 70)
    print("# SIMULATION 2: DNS Layer 7 DDoS")
    print("#" * 70 + "\n")
    kg_dns, anomalies_dns = simulate_dns_layer7_attack()
