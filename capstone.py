import smtplib
import conf,json,time
from boltiot import Sms,Email,Bolt
import math, statistics


minimum_limit = 50
maximum_limit = 90

mybolt = Bolt(conf.API_KEY, conf.DEVICE_ID)
mailer = Email(conf.MAILGUN_API_KEY, conf.SANDBOX_URL, conf.SENDER_EMAIL, conf.RECIPIENT_EMAIL)
sms = Sms(conf.SSID, conf.AUTH_TOKEN, conf.TO_NUMBER, conf.FROM_NUMBER)


def buzzer_alert():
        response = mybolt.digitalWrite("0","HIGH")
        data_b = json. loads (response)
        if data_b["success"]!=1:
                print("There was an error while sending a sound alert.",data_b["value"])
        time.sleep (30)
        response = mybolt.digitalWrite("0","LOW")


def compute_bounds(history_data,frame_size,factor):
    if len(history_data)<frame_size :
        return None

    if len(history_data)>frame_size :
        del history_data[0:len(history_data)-frame_size]
    Mn=statistics.mean(history_data)
    Variance=0
    for data in history_data :
        Variance += math.pow((data-Mn),2)
    Zn = factor * math.sqrt(Variance / frame_size)
    High_bound = history_data[frame_size-1]+Zn
    Low_bound = history_data[frame_size-1]-Zn
    return [High_bound,Low_bound]

history_data=[]



while True:
        print("Reading The Sensor Value: ")
        response = mybolt.analogRead('A0')
        data = json.loads(response)
        print ("Sensor value is: " + str(data['value']))
        try:
                sensor_value = int(data['value'])
                bound = compute_bounds(history_data,conf.FRAME_SIZE,conf.MUL_FACTOR)
                if not bound:
                        required_data_count=conf.FRAME_SIZE-len(history_data)
                        print("Not enough data to compute Z-score. Need ",required_data_count," more data points")
                        history_data.append(int(data['value']))
                        time.sleep(10)
                        continue

                try:
                        if sensor_value > bound[0] :
                                print("bound[0] = ",bound[0])
                                response = mailer.send_email("Alert!Temperature crossed the range", "The current temperature sensor value is " +str(sensor_value))
                                response2 = sms.send_sms("The Current temperature sensor value is " +str(sensor_value))
                                print("This is the response ",response)
                        elif sensor_value < bound[1]:
                                print("bound[1] = ",bound[1])
                                print ("Temperature is less than the minimum limit")
                                print("This is the response ",response)
                        history_data.append(sensor_value);
                        time.sleep(10)

                except Exception as e:
                        print ("Error",e)
                        continue

                #Email send if temprature crossed threshold
                if sensor_value > maximum_limit or sensor_value < minimum_limit:
                        print ("Tempurature Crosses Threshold")
                        buzzer_alert()
                        print(sensor_value)
                        response = mailer.send_email("Alert", "The current temperature sensor value is " +str(sensor_value))
                        response_text = json.loads(response.text)
                        response2 = sms.send_sms("The Current temperature sensor value is " +str(sensor_value)+"Please check the temperature and alert the people")
                        print("Response recieved from Mailgun: " + str(response_text['message']))
        except Exception as e:
                print ("Error occured: Below are the details")
                print (e)
                time.sleep(10)
