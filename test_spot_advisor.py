import os,stat
import sys
import boto3
import datetime
import json
import subprocess
import requests

def datetime_handler(x):
    if isinstance(x, datetime.datetime):
        return x.isoformat()
    raise TypeError("Unknown type")

def get_instance_list(args='--vcpus 2 --memory-min 4'):

    pwd = os.getcwd()

    filter_str = ' --deny-list [rmc][1-3]\.*|xargs'
    ec2list_cmd = pwd + '/' + 'ec2-instance-selector --max-results 300 -a x86_64 ' + args + filter_str
    
    result = subprocess.run(ec2list_cmd,shell=True,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    
    #somehow the returncode always = 0 , we have to use stderr to determine whether success or not
    if len(result.stderr) != 0:
        return []
        #raise Exception(str(result.stderr))
    
    ec2list = str(result.stdout)
    return ec2list.split(' ')


def get_spot_price_list(instance_list,region = 'ap-northeast-1'):

    ec2client = boto3.client(service_name='ec2',region_name = region)

    prices = ec2client.describe_spot_price_history(
        #InstanceTypes = instance_list,
        StartTime = datetime.datetime.now(),
        EndTime = datetime.datetime.now(),
        #AvailabilityZone='ap-northeast-1a',
        ProductDescriptions = ['Linux/UNIX']
        )

    #print(json.dumps(prices['SpotPriceHistory'],default=datetime_handler,indent=4))
    print(prices)
    return prices['SpotPriceHistory']

def get_spot_advisor_data(interrupt_ratio_index = 0,saving = 50,region = 'ap-northeast-1'):
    '''
    Get Spot Advisor json data
    :param interrupt_ratio_index: at least how frequent spot will be interrupted in past 30 days
    :param saving: at least how much could be saved compare to OD.
    :param region: which region you want to fetch
    
    :return: instance dict
    :rtype: dict
    
    return example:
    {'r5a.xlarge': {
        's': 73, 
        'r': 1, 
        'cores': 4, 
        'emr': True, 
        'ram_gb': 32.0
        },
        ...
    }

    '''
    url = 'https://spot-bid-advisor.s3.amazonaws.com/spot-advisor-data.json'

    resp = requests.get(url)
    if resp.status_code != 200:
        raise Exception('Unable to get spot advisor data. HTTP Error Code:{}'.format(resp.status_code))
    
    spot_advisor_json = json.loads(resp.text)

    instance_dict = spot_advisor_json['spot_advisor'][region]['Linux']
    instance_dict_filtered = {}

    # key = instance type value = {s: saving,r: interrupt_ratio_index}
    for key,value in instance_dict.items():
        if value['s'] >= saving and value['r'] <= interrupt_ratio_index:
            #_instance[key]
            value['cores'] = spot_advisor_json['instance_types'][key]['cores']
            value['emr'] = spot_advisor_json['instance_types'][key]['emr']
            value['ram_gb'] = spot_advisor_json['instance_types'][key]['ram_gb']
            instance_dict_filtered[key] = value     

    return instance_dict_filtered




def lambda_handler(event, context):
    # TODO implement

    print(event)
    print(context)
    
    args = ' '
    args_flag = 0
    region = 'ap-northeast-1'

    if len(event['vcpus']) != 0:
        args_flag = 1
        args += ' --vcpus ' + event['vcpus']
    if len(event['vcpus-min']) != 0:
        args_flag = 1
        args += ' --vcpus-min ' + event['vcpus-min']
    if len(event['memory']) != 0:
        args_flag = 1
        args += ' --memory ' + event['memory']
    if len(event['memory-min']) != 0:
        args_flag = 1
        args += ' --memory-min ' + event['memory-min']
    if len(event['memory-max']) != 0:
        args_flag = 1
        args += ' --memory-max ' + event['memory-max']
    if len(event['vcpus-max']) != 0:
        args_flag = 1
        args += ' --vcpus-max ' + event['vcpus-max']
    if len(event['region']) != 0:
        args_flag = 1
        args += ' --region ' + event['region']
        region = event['region']
   
    client = boto3.client('ec2',region_name=region)

    output = client.describe_regions()

    region_list = []
    [region_list.append(x['RegionName']) for x in output['Regions']]

    if args_flag == 0 or region not in region_list:
        return {"errMessage":"Please specify at least one parameter(vcpus/memory) and region)."}

    #args = sys.argv[1:]
    #args = ['--vcpus','2','--memory-min','4']
    
    print('args: ' + args)

    ec2list = get_instance_list(args)

    #return empty map to avoid detail error message in http response.
    if len(ec2list) == 0:
        return {}
    #ec2list = get_instance_list(' '.join(args))
    spot_summary = get_spot_price_list(ec2list,region)
    #print(spot_summary)

    print('region:' + region)
    instance_dict = get_spot_advisor_data(1,50,region)
    result_dict = {}

    for key,value in instance_dict.items():

        value['spot'] = []
        for spot in spot_summary:
            if key == spot['InstanceType']:
                _spot_element = {}
                _spot_element['AvailabilityZone'] = spot['AvailabilityZone']
                #Montly price
                _spot_element['SpotPrice'] = round(float(spot['SpotPrice'])*720,2)
                #Hourly price
                #_spot_element['SpotPrice'] = spot['SpotPrice']
                _spot_element['Timestamp'] = spot['Timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                value['spot'].append(_spot_element)
                result_dict[key] = value

    #sort output according to saving compare to OD,but result became a list not map
    sorted_result_dict = sorted(result_dict.items(),key=lambda x:x[1]['s'])
    print(result_dict)
    return result_dict
lambda_handler({"vcpus":"4","memory":"8","vcpus-min":"","memory-min":"","vcpus-max":"","memory-max":"","region":"ap-southeast-1"},"ivan")
