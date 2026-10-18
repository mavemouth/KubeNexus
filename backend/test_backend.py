import requests

base = 'http://localhost:8000/api/v1'

print('--- 1. Health ---')
r = requests.get('http://localhost:8000/health')
print('Status:', r.status_code, r.json())

print('\n--- 2. Clusters ---')
r = requests.get(f'{base}/clusters')
print('Clusters count:', len(r.json()))
assert len(r.json()) >= 4

print('\n--- 3. Workloads ---')
r = requests.get(f'{base}/workloads')
print('Workloads count:', len(r.json()))
assert len(r.json()) >= 7

print('\n--- 4. Cost Summary ---')
r = requests.get(f'{base}/cost/summary')
print('Cost Summary:', r.json())
assert r.json()['monthlySpend'] > 0

print('\n--- 5. Trigger Analysis for Workload ---')
r = requests.post(f'{base}/workloads/wl-payment-service/analysis')
print('Analysis:', r.status_code, r.json()['status'])
rec = r.json()['recommendation']
rec_id = rec['id']
print('Generated Rec ID:', rec_id, 'Recommended CPU:', rec['recommendedCpuRequest'], 'Savings:', rec['estimatedMonthlySavings'])

print('\n--- 6. Approve Recommendation ---')
r = requests.post(f'{base}/recommendations/{rec_id}/approve')
print('Approve:', r.status_code, r.json()['status'])
assert r.json()['status'] == 'Approved'

print('\n--- 7. Apply Recommendation ---')
r = requests.post(f'{base}/recommendations/{rec_id}/apply')
print('Apply:', r.status_code, r.json()['status'])
assert r.json()['status'] == 'Applied'

print('\n--- 8. Prevent Duplicate Apply ---')
r_dup = requests.post(f'{base}/recommendations/{rec_id}/apply')
print('Duplicate Apply Prevention (should be 400):', r_dup.status_code, r_dup.json())
assert r_dup.status_code == 400

print('\n--- 9. Verify Workload Updated ---')
r = requests.get(f'{base}/workloads/wl-payment-service')
print('Workload after apply:', r.json()['cpuRequest'], r.json()['status'], 'utilization:', r.json()['cpuUtilizationPct'])
assert r.json()['status'] == 'Healthy'

print('\n--- 10. Audit Log ---')
r = requests.get(f'{base}/audit-events')
events = r.json()
print('Audit events count:', len(events))
print('Latest Audit Action:', events[0]['action'], 'for', events[0]['workloadName'])
assert events[0]['action'] == 'Applied'

print('\n--- 11. Post-Change Evaluation ---')
r = requests.get(f'{base}/evaluations')
evals = r.json()
print('Evaluations count:', len(evals))
print('Latest Evaluation:', evals[0]['workloadName'], 'before:', evals[0]['beforeCpuRequest'], 'after:', evals[0]['afterCpuRequest'])

print('\n--- 12. Alerts Resolution ---')
r = requests.get(f'{base}/alerts')
alerts = r.json()
print('Active alerts count:', len(alerts))
first_id = alerts[0]['id']
r_res = requests.post(f'{base}/alerts/{first_id}/resolve')
print('Resolved alert:', r_res.status_code, r_res.json()['status'])
assert r_res.json()['status'] == 'Resolved'

print('\nALL BACKEND API AND CORE WORKFLOW TESTS PASSED SUCCESSFULLY!')
