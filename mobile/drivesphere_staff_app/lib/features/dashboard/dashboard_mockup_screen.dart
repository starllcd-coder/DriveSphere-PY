import 'package:flutter/material.dart';

import '../../widgets/staff_scaffold.dart';

class DashboardMockupScreen extends StatelessWidget {
  const DashboardMockupScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return StaffScaffold(
      title: 'Dashboard Mockup',
      body: ListView(
        children: const [
          _TopSummaryCard(),
          SizedBox(height: 12),
          _SectionTitle(
            title: 'Today Overview',
            subtitle: 'Operational snapshot',
          ),
          SizedBox(height: 8),
          _KpiGrid(),
          SizedBox(height: 14),
          _SectionTitle(
            title: 'Fleet Activity',
            subtitle: 'Utilization & vehicle state',
          ),
          SizedBox(height: 8),
          _FleetBarsCard(),
          SizedBox(height: 14),
          _SectionTitle(
            title: 'Revenue Trend',
            subtitle: 'Last 7 days',
          ),
          SizedBox(height: 8),
          _RevenueLineCard(),
          SizedBox(height: 14),
          _SectionTitle(
            title: 'Pending Actions',
            subtitle: 'Items needing staff follow-up',
          ),
          SizedBox(height: 8),
          _ActionListCard(),
        ],
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String title;
  final String subtitle;

  const _SectionTitle({required this.title, required this.subtitle});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w700,
            color: Color(0xFF1D3559),
          ),
        ),
        const SizedBox(height: 2),
        Text(
          subtitle,
          style: const TextStyle(
            fontSize: 13,
            color: Color(0xFF66708B),
          ),
        ),
      ],
    );
  }
}

class _TopSummaryCard extends StatelessWidget {
  const _TopSummaryCard();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        gradient: const LinearGradient(
          colors: [Color(0xFF1F4E8C), Color(0xFF2F69B5)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Good Morning, Admin',
            style: TextStyle(
              color: Colors.white,
              fontWeight: FontWeight.w700,
              fontSize: 18,
            ),
          ),
          SizedBox(height: 6),
          Text(
            'Branch: Dubai Marina - Shift: 08:00 - 18:00',
            style: TextStyle(color: Color(0xD9FFFFFF), fontSize: 13),
          ),
          SizedBox(height: 10),
          Row(
            children: [
              _TinyStat(label: 'Open Tasks', value: '12'),
              SizedBox(width: 8),
              _TinyStat(label: 'Due Returns', value: '7'),
              SizedBox(width: 8),
              _TinyStat(label: 'New Leads', value: '5'),
            ],
          ),
        ],
      ),
    );
  }
}

class _TinyStat extends StatelessWidget {
  final String label;
  final String value;

  const _TinyStat({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          color: const Color(0x26FFFFFF),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: const Color(0x40FFFFFF)),
        ),
        child: Column(
          children: [
            Text(
              value,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.w700,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              style: const TextStyle(color: Color(0xD9FFFFFF), fontSize: 11),
            ),
          ],
        ),
      ),
    );
  }
}

class _KpiGrid extends StatelessWidget {
  const _KpiGrid();

  @override
  Widget build(BuildContext context) {
    return const Column(
      children: [
        Row(
          children: [
            Expanded(
              child: _KpiTile(
                title: 'Bookings',
                value: '84',
                delta: '+11%',
                icon: Icons.event_note_rounded,
              ),
            ),
            SizedBox(width: 8),
            Expanded(
              child: _KpiTile(
                title: 'Active Rentals',
                value: '41',
                delta: '+5%',
                icon: Icons.directions_car_filled_rounded,
              ),
            ),
          ],
        ),
        SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: _KpiTile(
                title: 'Revenue',
                value: 'AED 54.8K',
                delta: '+8%',
                icon: Icons.payments_rounded,
              ),
            ),
            SizedBox(width: 8),
            Expanded(
              child: _KpiTile(
                title: 'Pending Balance',
                value: 'AED 12.3K',
                delta: '-2%',
                icon: Icons.warning_amber_rounded,
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _KpiTile extends StatelessWidget {
  final String title;
  final String value;
  final String delta;
  final IconData icon;

  const _KpiTile({
    required this.title,
    required this.value,
    required this.delta,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    final positive = delta.startsWith('+');
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xCCFFFFFF),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0x55FFFFFF)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 18, color: const Color(0xFF1F4E8C)),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  title,
                  style: const TextStyle(
                    color: Color(0xFF4D5976),
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            value,
            style: const TextStyle(
              color: Color(0xFF1C3B67),
              fontWeight: FontWeight.w700,
              fontSize: 19,
            ),
          ),
          const SizedBox(height: 6),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color:
                  positive ? const Color(0x1F2EAD67) : const Color(0x1FD84A4A),
              borderRadius: BorderRadius.circular(999),
            ),
            child: Text(
              delta,
              style: TextStyle(
                color: positive
                    ? const Color(0xFF1B8F55)
                    : const Color(0xFFC53A3A),
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _FleetBarsCard extends StatelessWidget {
  const _FleetBarsCard();

  @override
  Widget build(BuildContext context) {
    return const _CardShell(
      child: Column(
        children: [
          _BarRow(label: 'Rented', value: 0.62, color: Color(0xFF2E7BE6)),
          SizedBox(height: 10),
          _BarRow(label: 'Available', value: 0.24, color: Color(0xFF1FA173)),
          SizedBox(height: 10),
          _BarRow(label: 'Maintenance', value: 0.14, color: Color(0xFFD18C2F)),
        ],
      ),
    );
  }
}

class _BarRow extends StatelessWidget {
  final String label;
  final double value;
  final Color color;

  const _BarRow({
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final pct = (value * 100).toStringAsFixed(0);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(
              label,
              style: const TextStyle(
                  fontWeight: FontWeight.w600, color: Color(0xFF475677)),
            ),
            const Spacer(),
            Text(
              '$pct%',
              style: const TextStyle(
                  fontWeight: FontWeight.w700, color: Color(0xFF2A3B62)),
            ),
          ],
        ),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(999),
          child: LinearProgressIndicator(
            minHeight: 9,
            value: value,
            backgroundColor: const Color(0xFFE4EAF4),
            valueColor: AlwaysStoppedAnimation(color),
          ),
        ),
      ],
    );
  }
}

class _RevenueLineCard extends StatelessWidget {
  const _RevenueLineCard();

  @override
  Widget build(BuildContext context) {
    return const _CardShell(
      child: SizedBox(
        height: 160,
        child: CustomPaint(
          painter: _SimpleLinePainter(),
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: 8, vertical: 6),
            child: Align(
              alignment: Alignment.bottomCenter,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('Mon',
                      style: TextStyle(fontSize: 11, color: Color(0xFF6C7390))),
                  Text('Tue',
                      style: TextStyle(fontSize: 11, color: Color(0xFF6C7390))),
                  Text('Wed',
                      style: TextStyle(fontSize: 11, color: Color(0xFF6C7390))),
                  Text('Thu',
                      style: TextStyle(fontSize: 11, color: Color(0xFF6C7390))),
                  Text('Fri',
                      style: TextStyle(fontSize: 11, color: Color(0xFF6C7390))),
                  Text('Sat',
                      style: TextStyle(fontSize: 11, color: Color(0xFF6C7390))),
                  Text('Sun',
                      style: TextStyle(fontSize: 11, color: Color(0xFF6C7390))),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _SimpleLinePainter extends CustomPainter {
  const _SimpleLinePainter();

  @override
  void paint(Canvas canvas, Size size) {
    final grid = Paint()
      ..color = const Color(0xFFE8EDF7)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;
    for (var i = 1; i <= 4; i++) {
      final y = (size.height - 24) * (i / 5);
      canvas.drawLine(Offset(0, y), Offset(size.width, y), grid);
    }

    final points = <Offset>[
      Offset(0, size.height * 0.65),
      Offset(size.width * 0.16, size.height * 0.56),
      Offset(size.width * 0.32, size.height * 0.60),
      Offset(size.width * 0.48, size.height * 0.43),
      Offset(size.width * 0.64, size.height * 0.38),
      Offset(size.width * 0.80, size.height * 0.45),
      Offset(size.width, size.height * 0.30),
    ];

    final line = Paint()
      ..color = const Color(0xFF2A6BC9)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3;

    final fill = Paint()
      ..shader = const LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [Color(0x663D81E6), Color(0x003D81E6)],
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height))
      ..style = PaintingStyle.fill;

    final linePath = Path()..moveTo(points.first.dx, points.first.dy);
    for (var i = 1; i < points.length; i++) {
      final midX = (points[i - 1].dx + points[i].dx) / 2;
      linePath.quadraticBezierTo(
          midX, points[i - 1].dy, points[i].dx, points[i].dy);
    }

    final fillPath = Path.from(linePath)
      ..lineTo(size.width, size.height)
      ..lineTo(0, size.height)
      ..close();

    canvas.drawPath(fillPath, fill);
    canvas.drawPath(linePath, line);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _ActionListCard extends StatelessWidget {
  const _ActionListCard();

  @override
  Widget build(BuildContext context) {
    return const _CardShell(
      child: Column(
        children: [
          _ActionRow(
            color: Color(0xFFD18C2F),
            title: '7 bookings due for return in 2 hours',
            subtitle: 'Front desk should initiate reminders',
          ),
          Divider(height: 18),
          _ActionRow(
            color: Color(0xFF2E7BE6),
            title: '3 contracts awaiting approval',
            subtitle: 'Manager authorization required',
          ),
          Divider(height: 18),
          _ActionRow(
            color: Color(0xFF1FA173),
            title: '5 maintenance tasks completed',
            subtitle: 'Ready for quality check',
          ),
        ],
      ),
    );
  }
}

class _ActionRow extends StatelessWidget {
  final Color color;
  final String title;
  final String subtitle;

  const _ActionRow({
    required this.color,
    required this.title,
    required this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 10,
          height: 10,
          margin: const EdgeInsets.only(top: 6),
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                  color: Color(0xFF2D3E62),
                ),
              ),
              const SizedBox(height: 2),
              Text(
                subtitle,
                style: const TextStyle(
                  fontSize: 12,
                  color: Color(0xFF6A7390),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _CardShell extends StatelessWidget {
  final Widget child;

  const _CardShell({required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xCCFFFFFF),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0x55FFFFFF)),
      ),
      child: child,
    );
  }
}
