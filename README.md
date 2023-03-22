## Payment Gateway Bidvest

Bidvest Payment Gateway Intergration App for Frappe and ERPNext.

> Disclaimer: This app is NOT an official app of Bidvest. Development of the app was guided by the Bidvest Custom Integration documentation and the ERPNext process flows. It is your responsibility to review and ensure your process flows and security standards are met. The author will not be held reponsible for any loss as stipulated in the MIT License.



Supported Frappe & ERPNext versions: version-14


Supported currencies = ZAR (South African Rand)

Supported process flows: Web forms and payment requests.

### Installation
bench --site [sitename] get-app  --branch [release tag]

bench --site [sitename] install-app payment_gateway_Bidvest

bench --site [sitename] migrate

### Web Form process flow
![Web form flow](./Web-form-flow.jpg)


### Payment Request process flow
![Payment Request flow](./Payment-request-flow.jpg)


### Doctype description

Doctype: Bidvest Settings

The first section is necessary to ensure successful integration with Bidvest

Requirement: A merchant account with Bidvest.
![Payment Integration](./payfast-settings-form.JPG)

The second optional section is necessary to ensure successful integration with ERPNext Accounts module

Requirement: ERPNext app installed
![Accounts Integration](./payfast-settings-form-accounts.JPG)


#### License

MIT
