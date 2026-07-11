class BranchModel {
  final int id;
  final String name;
  final String code;

  const BranchModel({
    required this.id,
    required this.name,
    required this.code,
  });

  factory BranchModel.fromJson(Map<String, dynamic> json) {
    return BranchModel(
      id: (json['id'] as num?)?.toInt() ?? 0,
      name: json['name']?.toString() ?? '',
      code: json['code']?.toString() ?? '',
    );
  }
}

