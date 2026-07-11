import 'branch_model.dart';

class StaffProfile {
  final int id;
  final String email;
  final String fullName;
  final String roleCode;
  final List<String> permissions;
  final BranchModel? defaultBranch;

  const StaffProfile({
    required this.id,
    required this.email,
    required this.fullName,
    required this.roleCode,
    required this.permissions,
    required this.defaultBranch,
  });

  factory StaffProfile.fromJson(Map<String, dynamic> json) {
    final role = json['role'] as Map<String, dynamic>?;
    final branch = json['default_branch'] as Map<String, dynamic>?;
    return StaffProfile(
      id: (json['id'] as num?)?.toInt() ?? 0,
      email: json['email']?.toString() ?? '',
      fullName: json['full_name']?.toString() ?? '',
      roleCode: role?['code']?.toString() ?? 'VIEWER',
      permissions: ((json['permissions'] as List?) ?? const [])
          .map((item) => item.toString())
          .toList(),
      defaultBranch: branch == null ? null : BranchModel.fromJson(branch),
    );
  }

  bool can(String perm) => permissions.contains(perm);
}

