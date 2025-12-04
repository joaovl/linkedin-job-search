import json

try:
    with open('Engineering_Manager__Londonuk.json', encoding='utf-8') as f:
        data = json.load(f)
    
    if data:
        job = data[0]
        print("First job:")
        print(f"  Title: {job['title']}")
        print(f"  Company: {job['company']}")
        print(f"  Description: {job.get('description', 'MISSING')[:100]}...")
        
        # Count how many have descriptions
        desc_count = sum(1 for j in data if j.get('description') and not j.get('description').startswith('Failed') and not j.get('description').startswith('Description not'))
        print(f"\n{desc_count}/{len(data)} jobs have descriptions")
except Exception as e:
    print(f"Error: {e}")
