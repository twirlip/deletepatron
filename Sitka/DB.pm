#!/usr/bin/perl
package Sitka::DB;
use DBI;

# TODO: integrate this with fm_IDL.xml
# database connection
my ($db_driver,$db_host,$db_name,$db_user,$db_pw) =
  #('Pg','192.168.0.210','evergreen','evergreen','f00bcp1n35b4r');
  ('Pg','192.168.0.219','husk','postgres','bcp1n35f00b4r');
my $dsn = "dbi:$db_driver:host=$db_host;dbname=$db_name";
$dbh = DBI->connect($dsn,$db_user,$db_pw);
$dbh->do("BEGIN;") or die "Could not begin database transaction $dsn"; 

sub lookup {
  my $sql = shift @_;
  my $sth = $dbh->prepare($sql);
  $sth->execute(@_);
  my @result = $sth->fetchrow_array();
  $sth->finish;
  return @result;
}

1; # perl is stupid.
