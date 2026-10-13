import json
from pathlib import Path
import unittest

class AWSTemplateTests(unittest.TestCase):
    def test_network_and_instance_boundaries(self):
        t=json.loads((Path(__file__).resolve().parents[1]/'deploy/aws/instance.json').read_text())
        r=t['Resources']; instance=r['Instance']['Properties']
        self.assertEqual(instance['MetadataOptions']['HttpTokens'],'required')
        self.assertTrue(instance['BlockDeviceMappings'][0]['Ebs']['Encrypted'])
        self.assertFalse(instance['BlockDeviceMappings'][0]['Ebs']['DeleteOnTermination'])
        ports={x['FromPort'] for x in r['WebSecurityGroup']['Properties']['SecurityGroupIngress']}
        self.assertEqual(ports,{80,443})
        self.assertNotIn('KeyName',instance)
        self.assertEqual(r['PublicAddress']['Type'],'AWS::EC2::EIP')
        user_data=instance['UserData']['Fn::Base64']['Fn::Sub']
        self.assertIn('${SourceCommit}',user_data)
        self.assertNotIn('/pair?ticket=',user_data)
        self.assertNotIn('CLIENT_SECRET',json.dumps(t))
        self.assertIn('CAPABILITY_IAM',(Path(__file__).resolve().parents[1]/'docs/AWS-ONBOARDING.md').read_text())

if __name__=='__main__':unittest.main()
