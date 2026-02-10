# Toil Tracker v0.1.1 - Enhanced DevOps Toil Detection

🔧 **Advanced version** with enhanced analytics, integrations, and performance optimizations while preserving backward compatibility.

## 🚀 What's New in v0.1.1

### ✨ **Enhanced Features**
- **Advanced Pattern Detection**: Regex + file-based analysis
- **Team Analytics**: Author-based insights and workload analysis  
- **Cost Estimation**: Calculate financial impact of toil
- **Configuration System**: YAML-based customization
- **Multi-Platform Integrations**: Slack, JIRA, GitHub Actions
- **Performance Optimizations**: Caching and parallel processing

### 🛠️ **Technical Improvements**
- **Enhanced CLI** with subcommands (`scan`, `report`, `benchmark`)
- **Export Functionality** (JSON, CSV formats)
- **Time-based Analytics**: Peak hours, trends, velocity
- **Automation ROI** calculations
- **Database Optimization** with indexing

## 📦 Installation

### **Option 1: Enhanced Version (Recommended)**
```bash
pip install git+https://github.com/amrutp24/toil-tracker@0.1.1
```

### **Option 2: Stable Original (v0.1.0)**
```bash
pip install git+https://github.com/amrutp24/toil-tracker@main
```

## 🎯 Enhanced Usage

### **Advanced Scanning**
```bash
# Enhanced single repo scan
toil-tracker scan ./my-repo --days 60 --verbose

# Parallel multi-repo scan
toil-tracker scan --multiple --repos repos.txt

# Use custom configuration
toil-tracker scan ./repo --config toil-config.yaml
```

### **Powerful Reporting**
```bash
# Generate detailed report
toil-tracker report --days 60 --export json --output toil-report.json

# Benchmark time periods
toil-tracker benchmark --days 30
```

### **Initialize Configuration**
```bash
# Create custom config file
toil-tracker init --config my-toil-config.yaml
```

### **Launch Analytics Dashboard**
```bash
# Enhanced dashboard with new metrics
toil-tracker dashboard
```

### **Analytics Module**
```bash
# Run advanced analytics
toil-analytics
```

## 📊 New Analytics Capabilities

### **Time-Based Insights**
- **Peak Hours**: Identify busiest operational times
- **Trend Analysis**: Detect increasing/decreasing toil patterns  
- **Velocity Metrics**: Calculate toil acceleration
- **Anomaly Detection**: Flag unusual spikes

### **Team Insights**
- **Workload Distribution**: Identify team imbalances
- **Task Specialization**: See who handles what types
- **Collaboration Analysis**: Cross-repo contributions

### **Cost Analysis**
```python
# Example: Financial impact
{
    'total_hours': 45.2,
    'total_cost': 4520.0,
    'daily_average_hours': 1.5,
    'automation_roi': {
        'high_automation': {'potential_savings': 2400.0},
        'medium_automation': {'potential_savings': 800.0}
    }
}
```

## 🔧 Configuration System

### **Custom Patterns** (toil-config.yaml)
```yaml
patterns:
  manual_deploy:
    keywords: ["deploy", "production deploy"]
    regex: ["deploy.*production", "prod.*release"]
    file_patterns: ["deploy*.sh", "k8s/*.yaml"]
    exclude: ["test", "staging"]
    severity_multiplier: 1.2

severity:
  high: ["emergency", "critical", "outage"]
  medium: ["hotfix", "production"]
  low: ["config", "restart"]
```

### **Analytics Settings**
```yaml
analytics:
  cost_estimation:
    default_hourly_rate: 100.0
    time_per_event:
      HIGH: 4.0
      MEDIUM: 2.0
      LOW: 1.0
```

## 🔌 Integrations Setup

### **Slack Notifications**
```yaml
integrations:
  slack:
    enabled: true
    webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK"
    channel: "#devops-alerts"
    trigger_conditions:
      high_severity_count: 3
      daily_toil_threshold: 10
```

### **JIRA Integration**
```yaml
  jira:
    enabled: true
    server_url: "https://your-company.atlassian.net"
    username: "devops-bot@company.com"
    api_token: "your-api-token"
    project_key: "DEV"
    priority_mapping:
      HIGH: "Highest"
      MEDIUM: "High"
```

### **GitHub Issues**
```yaml
  github:
    enabled: true
    token: "ghp_your-token"
    create_issues: true
    labels: ["toil", "automation-opportunity"]
```

## 📈 Performance Features

### **Caching**
```bash
# Automatic caching enabled
toil-tracker scan ./repo  # First scan: 10s
toil-tracker scan ./repo  # Cached scan: 0.5s
```

### **Parallel Processing**
```bash
# Scan 20 repos in parallel
toil-tracker scan --multiple --repos large-repo-list.txt
```

### **Database Optimization**
- Automatic indexing for faster queries
- Configurable cleanup (default: 90 days)
- Vacuum and analyze optimizations

## 🎯 Real-World Examples

### **Enterprise Usage**
```bash
# Weekly team report
toil-tracker report --days 7 --export json | jq '.total_cost'
# Output: 2450.00

# Identify automation opportunities  
toil-analytics | grep "High Toil Volume"
```

### **DevOps Team**
```bash
# Track team workload
toil-tracker scan ./production --days 30
toil-tracker benchmark --days 30

# Alert on high severity events
# Automatic Slack/JIRA notifications
```

## 📋 Migration from v0.1.0

### **Safe Upgrade**
```bash
# v0.1.0 remains unchanged and stable
# v0.1.1 adds new features without breaking changes

# Test new version
toil-tracker@0.1.1 scan ./test-repo

# Rollback if needed  
pip install git+https://github.com/amrutp24/toil-tracker@main
```

### **Database Migration**
- **v0.1.0**: Uses `toil.db`
- **v0.1.1**: Uses `toil_v2.db` (separate, no migration needed)
- **Data compatibility**: Export from old, import to new if desired

## 🔍 Advanced Detection Patterns

### **New Pattern Types**
- **kubernetes**: Pod crashes, deployment rollbacks
- **security**: CVE patches, vulnerability fixes
- **pipeline_issue**: CI/CD failures, build breaks

### **Enhanced Context**
```bash
# File-based detection
# Commit changes k8s/deployment.yaml + "restart" message
# = kubernetes task type with high confidence
```

## 📊 Sample Outputs

### **Enhanced CLI Output**
```
🔍 Scanning ./production...
✅ Found 23 toil events (12 cached)

📊 Toil Summary (last 30 days):
  manual_deploy: 8 total
    HIGH: 4, MEDIUM: 3, LOW: 1
  manual_fix: 6 total  
    HIGH: 3, MEDIUM: 2, LOW: 1
  kubernetes: 4 total
    HIGH: 2, MEDIUM: 2

💰 Cost Impact: $2,340.00 (23.4 hours)
🎯 Automation ROI: $1,872.00 potential savings
```

### **Analytics Dashboard**
- Real-time toil velocity charts
- Team workload heatmaps  
- Cost trend analysis
- Automation ROI projections

## 🛡️ Security & Privacy

- **No API keys** stored in code
- **Local data processing** - no data sent to external servers
- **Configurable integrations** - opt-in external services
- **MIT License** - free for commercial use

## 🤝 Contributing

### **v0.1.1 Development**
```bash
# Setup development environment
git clone https://github.com/amrutp24/toil-tracker
cd toil-tracker/0.1.1
pip install -e .

# Run tests
python -m pytest tests/

# Test new patterns
toil-tracker scan ./test-repo --config test-config.yaml
```

### **Feature Areas**
- [ ] Additional pattern types
- [ ] More integrations (Teams, Discord)  
- [ ] Machine learning pattern detection
- [ ] Web dashboard improvements

## 📄 License

MIT License - same as v0.1.0

---

**🚀 Ready to enhance your DevOps workflow?**

**Start with v0.1.1 for advanced capabilities, or stick with v0.1.0 for stability.**