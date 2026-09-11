import 'package:flutter/material.dart';
import '../services/api_client.dart';
import 'home_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final email = TextEditingController();
  final password = TextEditingController();
  final api = ApiClient();
  bool loading = false;
  String? error;

  @override void dispose() { email.dispose(); password.dispose(); super.dispose(); }

  Future<void> signIn() async {
    if (email.text.trim().isEmpty || password.text.isEmpty) {
      setState(() => error = 'Enter your email and password.');
      return;
    }
    setState(() { loading = true; error = null; });
    try {
      await api.login(email.text, password.text);
      if (mounted) Navigator.pushReplacement(
        context, MaterialPageRoute(builder: (_) => HomeScreen(api: api)),
      );
    } catch (e) {
      if (mounted) setState(() => error = e.toString().replaceFirst('Exception: ', ''));
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    body: SafeArea(
      child: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(28),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 460),
            child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
              Image.asset('assets/petronexa_logo.png', height: 170, fit: BoxFit.contain),
              const SizedBox(height: 16),
              const Text('PETRONEXA', textAlign: TextAlign.center,
                style: TextStyle(fontSize: 28, fontWeight: FontWeight.w900, letterSpacing: 2)),
              const SizedBox(height: 6),
              const Text('Petroleum Engineering Intelligence Platform',
                textAlign: TextAlign.center, style: TextStyle(color: Colors.white60)),
              const SizedBox(height: 30),
              TextField(controller: email, keyboardType: TextInputType.emailAddress,
                decoration: const InputDecoration(labelText: 'Email')),
              const SizedBox(height: 14),
              TextField(controller: password, obscureText: true,
                decoration: const InputDecoration(labelText: 'Password')),
              const SizedBox(height: 16),
              if (error != null) Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Text(error!, textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.redAccent)),
              ),
              FilledButton.icon(
                onPressed: loading ? null : signIn,
                icon: loading ? const SizedBox(width: 18, height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.login),
                label: Text(loading ? 'Signing in…' : 'Sign in'),
              ),
              const SizedBox(height: 18),
              const Text('Engineering outputs are decision-support aids and must be reviewed by a qualified engineer.',
                textAlign: TextAlign.center, style: TextStyle(fontSize: 11, color: Colors.white38)),
            ]),
          ),
        ),
      ),
    ),
  );
}
