# Toil Tracker

🔧 **Detect, visualize, and reduce DevOps toil** - Installable CLI tool for tracking repetitive operational work

## 🚀 Quick Install

```bash
pip install git+https://github.com/amrutp24/toil-tracker
```

## 📱 Usage

### Scan a repository for toil:
```bash
toil-tracker scan /path/to/your/repo
toil-tracker scan . --days 60
```

### View toil summary:
```bash
toil-tracker summary
toil-tracker summary --days 30
```

### Launch web dashboard:
```bash
toil-tracker dashboard
```

## 🎯 What it Detects

Automatically scans Git commit messages for toil patterns:

- **manual_deploy** - Manual deployment activities
- **manual_fix** - Emergency fixes and hotfixes  
- **revert** - Rollbacks and reverts
- **env_setup** - Environment configuration work
- **restart** - Service restarts/reboots

## 📊 Example Output

```
Scanning /myproject for toil patterns...
✅ Found 15 toil events

Breakdown:
  manual_deploy: 6
  manual_fix: 4
  restart: 3
  env_setup: 2

Toil Summary (last 30 days):
----------------------------------------
manual_deploy: 6 total
  HIGH: 3
  MEDIUM: 2
  LOW: 1
manual_fix: 4 total
  HIGH: 2
  MEDIUM: 1
  LOW: 1
```

## 🌟 Why This Matters

**30% of engineering time is spent on toil** - manual, repetitive work that provides no lasting value. This tool helps you:

1. **Identify** what repetitive work your team is doing
2. **Prioritize** automation opportunities  
3. **Track** reduction in operational overhead
4. **Make data-driven** DevOps decisions

## 🛠️ Development Install

```bash
git clone https://github.com/amrutp24/toil-tracker
cd toil-tracker
pip install -e .
```

## 📈 Next Steps

1. **Scan your repos** - Find your team's toil patterns
2. **Share findings** - Show colleagues the automation opportunities
3. **Automate the top 3** - Tackle highest-frequency toil first
4. **Track improvement** - Use dashboard to measure progress

## 🤝 Contributing

Found a toil pattern we missed? Open an issue or PR!

- Add detection patterns to `toil_detector.py`
- Improve visualizations in `dashboard.py`
- Share your toil reduction stories!

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

**⚡ Stop wasting time on toil. Start automating what matters.**