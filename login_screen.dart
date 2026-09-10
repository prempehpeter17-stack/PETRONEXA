import 'package:flutter/material.dart';
import '../services/api_client.dart';
import 'home_screen.dart';

class LoginScreen extends StatefulWidget { const LoginScreen({super.key}); @override State<LoginScreen> createState() => _LoginScreenState(); }
class _LoginScreenState extends State<LoginScreen> {
  final email = TextEditingController();
  final password = TextEditingController();
  final api = ApiClient();
  bool loading = false;
  String? error;
  Future<void> signIn() async {
    setState(() { loading = true; error = null; });
    try { await api.login(email.text.trim(), password.text); if (mounted) Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => HomeScreen(api: api))); }
    catch (e) { setState(() => error = e.toString().replaceFirst('Exception: ', '')); }
    finally { if (mounted) setState(() => loading = false); }
  }
  @override Widget build(BuildContext context) => Scaffold(body: Center(child: SingleChildScrollView(padding: const EdgeInsets.all(28), child: ConstrainedBox(constraints: const BoxConstraints(maxWidth: 460), child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
    Image.asset('assets/petronexa_logo.png', height: 190, fit: BoxFit.contain),
    const SizedBox(height: 24),
    TextField(controller: email, keyboardType: TextInputType.emailAddress, decoration: const InputDecoration(labelText: 'Email', border: OutlineInputBorder())), const SizedBox(height: 14),
    TextField(controller: password, obscureText: true, decoration: const InputDecoration(labelText: 'Password', border: OutlineInputBorder())), const SizedBox(height: 18),
    if (error != null) Padding(padding: const EdgeInsets.only(bottom: 12), child: Text(error!, style: const TextStyle(color: Colors.redAccent))),
    FilledButton(onPressed: loading ? null : signIn, child: Padding(padding: const EdgeInsets.all(12), child: Text(loading ? 'Signing in…' : 'Sign in'))),
    const SizedBox(height: 18), const Text('PetroNexa API', textAlign: TextAlign.center, style: TextStyle(fontSize: 12, color: Colors.white38)),
  ])))));
}
