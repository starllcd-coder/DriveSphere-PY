import 'package:flutter/material.dart';

import '../../models/vehicle_model.dart';
import '../../services/api_service.dart';
import '../../widgets/app_primary_button.dart';
import '../../widgets/app_snackbar.dart';

class ReviewScreen extends StatefulWidget {
  final VehicleModel vehicle;

  const ReviewScreen({
    super.key,
    required this.vehicle,
  });

  @override
  State<ReviewScreen> createState() => _ReviewScreenState();
}

class _ReviewScreenState extends State<ReviewScreen> {
  final ApiService _apiService = ApiService();
  final TextEditingController _commentController = TextEditingController();

  int _rating = 5;
  bool _loading = false;

  Future<void> _submit() async {
    setState(() => _loading = true);
    await _apiService.addReview(
      vehicleId: widget.vehicle.id,
      rating: _rating,
      comment: _commentController.text.trim(),
    );

    if (!mounted) return;
    setState(() => _loading = false);
    AppSnackBar.success(context, 'Thanks for sharing your review.');
    Navigator.pop(context);
  }

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F7FB),
      appBar: AppBar(
        title: const Text('Rate your experience'),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        children: [
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(20),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.vehicle.fullName,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  children: List.generate(5, (index) {
                    final value = index + 1;
                    return IconButton(
                      onPressed: () => setState(() => _rating = value),
                      icon: Icon(
                        value <= _rating
                            ? Icons.star_rounded
                            : Icons.star_outline_rounded,
                        color: const Color(0xFFD3AE52),
                      ),
                    );
                  }),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _commentController,
                  maxLines: 4,
                  decoration: InputDecoration(
                    labelText: 'Comment',
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                AppPrimaryButton(
                  label: 'Submit review',
                  loading: _loading,
                  onPressed: _submit,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
