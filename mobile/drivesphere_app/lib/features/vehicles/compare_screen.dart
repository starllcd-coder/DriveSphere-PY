import 'package:flutter/material.dart';

import '../../models/vehicle_model.dart';
import '../../services/api_service.dart';

class CompareScreen extends StatefulWidget {
  const CompareScreen({super.key});

  @override
  State<CompareScreen> createState() => _CompareScreenState();
}

class _CompareScreenState extends State<CompareScreen> {
  final ApiService _apiService = ApiService();
  List<VehicleModel> _vehicles = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadCompare();
  }

  Future<void> _loadCompare() async {
    final all = await _apiService.fetchVehicles();
    final ids = await _apiService.getCompareVehicleIds();

    if (!mounted) return;
    setState(() {
      _vehicles = all.where((e) => ids.contains(e.id)).toList();
      _loading = false;
    });
  }

  TableRow _row(String label, List<String> values) {
    return TableRow(
      children: [
        Padding(
          padding: const EdgeInsets.all(10),
          child: Text(label, style: const TextStyle(fontWeight: FontWeight.w700)),
        ),
        ...values.map((e) => Padding(
              padding: const EdgeInsets.all(10),
              child: Text(e),
            )),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final values = _vehicles;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Compare Vehicles'),
        actions: [
          IconButton(
            onPressed: () async {
              await _apiService.clearCompareVehicles();
              if (!mounted) return;
              setState(() => _vehicles = []);
            },
            icon: const Icon(Icons.delete_outline_rounded),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : values.length < 2
              ? const Center(child: Text('Add at least 2 vehicles to compare'))
              : SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Table(
                    border: TableBorder.all(color: const Color(0xFFE2E8F2)),
                    defaultColumnWidth: const IntrinsicColumnWidth(),
                    children: [
                      _row('Vehicle', values.map((e) => e.fullName).toList()),
                      _row('Company', values.map((e) => e.companyName).toList()),
                      _row('City', values.map((e) => e.city).toList()),
                      _row('Daily rate', values.map((e) => e.dailyRate.toStringAsFixed(2)).toList()),
                      _row('Deposit', values.map((e) => e.depositAmount.toStringAsFixed(2)).toList()),
                      _row('Rating', values.map((e) => e.rating.toStringAsFixed(1)).toList()),
                      _row('Category', values.map((e) => e.category).toList()),
                      _row('Transmission', values.map((e) => e.transmission).toList()),
                      _row('Seats', values.map((e) => e.seats.toString()).toList()),
                      _row('Fuel', values.map((e) => e.fuelType).toList()),
                    ],
                  ),
                ),
    );
  }
}