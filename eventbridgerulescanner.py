import boto3
import csv
import json

region = 'ap-southeast-1'
client = boto3.client('events', region_name=region)

# List all event buses
buses = []
next_token = None

while True:
    if next_token:
        response = client.list_event_buses(NextToken=next_token)
    else:
        response = client.list_event_buses()

    buses.extend(response['EventBuses'])
    next_token = response.get('NextToken')
    if not next_token:
        break

# For each bus → rules → targets (including input config)
all_rows = []

for bus in buses:
    bus_name = bus['Name']
    next_token = None

    while True:
        if next_token:
            rules_response = client.list_rules(EventBusName=bus_name, NextToken=next_token)
        else:
            rules_response = client.list_rules(EventBusName=bus_name)

        for rule in rules_response['Rules']:
            rule_name = rule.get('Name', '')
            rule_arn = rule.get('Arn', '')
            rule_state = rule.get('State', '')
            description = rule.get('Description', '')
            schedule = rule.get('ScheduleExpression', '')
            pattern = rule.get('EventPattern', '')
            role_arn = rule.get('RoleArn', '')
            managed_by = rule.get('ManagedBy', '')

            # Get targets for this rule
            target_response = client.list_targets_by_rule(Rule=rule_name, EventBusName=bus_name)
            targets = target_response.get('Targets', [])

            if not targets:
                all_rows.append([
                    bus_name, rule_name, rule_arn, rule_state, description,
                    schedule, pattern, role_arn, managed_by, '', '', ''
                ])
            else:
                for target in targets:
                    target_arn = target.get('Arn', '')
                    # Input: can be one of these
                    input_str = target.get('Input', '')
                    input_path = target.get('InputPath', '')
                    input_transformer = target.get('InputTransformer', '')

                    if input_transformer:
                        input_transformer = json.dumps(input_transformer)

                    all_rows.append([
                        bus_name, rule_name, rule_arn, rule_state, description,
                        schedule, pattern, role_arn, managed_by,
                        target_arn, input_str or input_path, input_transformer
                    ])

        next_token = rules_response.get('NextToken')
        if not next_token:
            break

# Export to CSV
with open('eventbridge_rules_with_targets.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow([
        'BusName', 'RuleName', 'RuleArn', 'State', 'Description',
        'ScheduleExpression', 'EventPattern', 'RoleArn', 'ManagedBy',
        'TargetArn', 'TargetInputOrPath', 'InputTransformer'
    ])
    writer.writerows(all_rows)

print("Export complete: eventbridge_rules_with_targets.csv")