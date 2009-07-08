#!/usr/bin/perl
package Sitka::DB;
use DBI;
use OpenSRF::System;
use OpenSRF::Utils::SettingsClient;

sub connect {
  # get database connection info from fm_IDL.xml
  OpenSRF::System->bootstrap_client( config_file => '/openils/conf/opensrf_core.xml'); 
  $settings  = OpenSRF::Utils::SettingsClient->new;
  $db_driver = $settings->config_value(apps => 'open-ils.storage' => 'app_settings' => 'databases' => 'driver');
  $db_host   = $settings->config_value(apps => 'open-ils.storage' => 'app_settings' => 'databases' => 'database' => 'host');
  $db_name   = $settings->config_value(apps => 'open-ils.storage' => 'app_settings' => 'databases' => 'database' => 'db');
  $db_user   = $settings->config_value(apps => 'open-ils.storage' => 'app_settings' => 'databases' => 'database' => 'user');
  $db_pw     = $settings->config_value(apps => 'open-ils.storage' => 'app_settings' => 'databases' => 'database' => 'pw');

  # database connection
  $dsn = "dbi:$db_driver:host=$db_host;dbname=$db_name";
  $dbh = DBI->connect($dsn,$db_user,$db_pw);
  $dbh->do("BEGIN;");
  return $dbh;
}

1; # perl is stupid.