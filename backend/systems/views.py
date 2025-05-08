from django.contrib.auth import get_user_model

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.generics import RetrieveUpdateAPIView, CreateAPIView
from rest_framework.views import APIView
from django.db.models import Q

from rest_framework.authtoken.models import Token

from .models import (
    DeveloperScore, 
    TraderScore, 
    CoinDRCScore, 
    CoinRugFlag,
    Coin, UserCoinHoldings, Trade, SolanaUser,
)

from .serializers import (
    DeveloperScoreSerializer, 
    TraderScoreSerializer, 
    CoinDRCScoreSerializer,
    CoinRugFlagSerializer,
    SolanaUserCreateSerializer,
    SolanaUserLoginSerializer,
    CoinSerializer, 
    UserCoinHoldingsSerializer, 
    TradeSerializer, 
    UserSerializer,
)

User = get_user_model()


class RestrictedViewset(viewsets.ModelViewSet):
    """
    API endpoint base class for ressiected views
    """
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']

class CoinViewSet(RestrictedViewset):
    """
    API endpoint for Coins
    """
    queryset = Coin.objects.all()
    serializer_class = CoinSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = 'address'
    
    @action(detail=True, methods=['get'])
    def holders(self, request, address=None):
        """Get all holders of a specific coin"""
        coin = self.get_object()
        holders = coin.holders.all()
        serializer = UserCoinHoldingsSerializer(holders, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def trades(self, request, address=None):
        """Get all trades for a specific coin"""
        coin = self.get_object()
        trades = coin.trades.all()
        serializer = TradeSerializer(trades, many=True)
        return Response(serializer.data)

class UserCoinHoldingsViewSet(RestrictedViewset):
    """
    API endpoint for User Coin Holdings
    """
    queryset = UserCoinHoldings.objects.all()
    serializer_class = UserCoinHoldingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter to only show the current user's holdings unless staff"""
        if self.request.user.is_staff:
            return UserCoinHoldings.objects.all()
        return UserCoinHoldings.objects.filter(user=self.request.user)

class TradeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Trades
    """
    queryset = Trade.objects.all()
    serializer_class = TradeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  # Will change to ReadOnly later
    lookup_field = 'id'  # Should eventually be changed to transaction_hash
    
    def perform_create(self, serializer):
        """Set user to current authenticated user"""
        serializer.save(user=self.request.user)
        
        # Update holdings after a trade
        coin = serializer.validated_data['coin']
        amount = serializer.validated_data['coin_amount']
        trade_type = serializer.validated_data['trade_type']
        
        # Get or create holdings for this user and coin
        holdings, created = UserCoinHoldings.objects.get_or_create(
            user=self.request.user,
            coin=coin,
            defaults={'amount_held': 0}
        )
        
        # Update holdings based on trade type
        if trade_type in ['BUY', 'COIN_CREATE']:
            holdings.amount_held += amount
        elif trade_type == 'SELL':
            if holdings.amount_held < amount:
                raise serializer.ValidationError("Not enough coins to sell")
            holdings.amount_held -= amount
            
        holdings.save()

class UserViewSet(RestrictedViewset): # check later
    """
    API endpoint for Solana Users
    """
    queryset = SolanaUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]#permissions.IsAuthenticated]
    lookup_field = 'wallet_address'
    
    @action(detail=True, methods=['get'])
    def holdings(self, request, wallet_address=None):
        """Get all coin holdings for a specific user"""
        user = self.get_object()
        # Check permissions - users can only see their own holdings
        if user.wallet_address != request.user.wallet_address and not request.user.is_staff:
            return Response(
                {"error": "You don't have permission to view this user's holdings"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        holdings = user.holdings.all()
        serializer = UserCoinHoldingsSerializer(holdings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def trades(self, request, wallet_address=None):
        """Get all trades for a specific user"""
        user = self.get_object()
        # Check permissions - users can only see their own trades
        if user.wallet_address != request.user.wallet_address and not request.user.is_staff:
            return Response(
                {"error": "You don't have permission to view this user's trades"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        trades = user.trades.all()
        serializer = TradeSerializer(trades, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def created_coins(self, request, wallet_address=None):
        """Get all coins created by a specific user"""
        user = self.get_object()
        coins = user.coins.all()
        from .serializers import CoinSerializer
        serializer = CoinSerializer(coins, many=True)
        return Response(serializer.data)

class RegisterView(CreateAPIView):
    queryset = SolanaUser.objects.all()
    serializer_class = SolanaUserCreateSerializer
    permission_classes = [permissions.AllowAny]

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SolanaUserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Create or get auth token
            token, _ = Token.objects.get_or_create(user=user)

            return Response({
                "message": "Login successful",
                "token": token.key,
                "wallet_address": user.wallet_address,
                "display_name": user.display_name,
                "bio": user.bio
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MeView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


# ViewSets
class DeveloperScoreViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for viewing developer reputation scores"""
    queryset = DeveloperScore.objects.all().order_by('-score')
    serializer_class = DeveloperScoreSerializer
    permission_classes = []#permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by minimum score
        min_score = self.request.query_params.get('min_score')
        if min_score and min_score.isdigit():
            queryset = queryset.filter(score__gte=int(min_score))
        
        # Filter by maximum score
        max_score = self.request.query_params.get('max_score')
        if max_score and max_score.isdigit():
            queryset = queryset.filter(score__lte=int(max_score))
        
        # Filter by developer address
        developer_address = self.request.query_params.get('developer')
        if developer_address:
            queryset = queryset.filter(developer__wallet_address__iexact=developer_address)
        
        # Filter to exclude rugged coins creators
        exclude_ruggers = self.request.query_params.get('exclude_ruggers')
        if exclude_ruggers and exclude_ruggers.lower() == 'true':
            queryset = queryset.filter(coins_rugged_count=0)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def top_developers(self, request):
        """Returns top 10 developers by score"""
        top_devs = self.get_queryset().filter(coins_created_count__gt=0)[:10]
        
        serializer = self.get_serializer(top_devs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_score(self, request):
        """Returns the authenticated user's developer score"""
        try:
            score = DeveloperScore.objects.get(developer=request.user)
            serializer = self.get_serializer(score)
            return Response(serializer.data)
        except DeveloperScore.DoesNotExist:
            return Response(
                {"detail": "No developer score found. Create a coin to establish your developer score."},
                status=status.HTTP_404_NOT_FOUND
            )

class TraderScoreViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for viewing trader reputation scores"""
    queryset = TraderScore.objects.all().order_by('-score')
    serializer_class = TraderScoreSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by minimum score
        min_score = self.request.query_params.get('min_score')
        if min_score and min_score.isdigit():
            queryset = queryset.filter(score__gte=int(min_score))
        
        # Filter by maximum score
        max_score = self.request.query_params.get('max_score')
        if max_score and max_score.isdigit():
            queryset = queryset.filter(score__lte=int(max_score))
        
        # Filter by trader address
        trader_address = self.request.query_params.get('trader')
        if trader_address:
            queryset = queryset.filter(trader__wallet_address__iexact=trader_address)
        
        # Filter by minimum trading activity
        min_trades = self.request.query_params.get('min_trades')
        if min_trades and min_trades.isdigit():
            queryset = queryset.filter(trades_count__gte=int(min_trades))
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def top_traders(self, request):
        """Returns top 10 traders by score"""
        top_traders = self.get_queryset().filter(trades_count__gt=5)[:10]
        serializer = self.get_serializer(top_traders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_score(self, request):
        """Returns the authenticated user's trader score"""
        try:
            score = TraderScore.objects.get(trader=request.user)
            serializer = self.get_serializer(score)
            return Response(serializer.data)
        except TraderScore.DoesNotExist:
            return Response(
                {"detail": "No trader score found. Make trades to establish your trader score."},
                status=status.HTTP_404_NOT_FOUND
            )

# class CoinDRCScoreViewSet(viewsets.ReadOnlyModelViewSet):
#     """API endpoint for viewing coin DRC scores"""
#     queryset = CoinDRCScore.objects.all().order_by('-score')
#     serializer_class = CoinDRCScoreSerializer
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get_queryset(self):
#         queryset = super().get_queryset()
        
#         # Filter by minimum score
#         min_score = self.request.query_params.get('min_score')
#         if min_score and min_score.isdigit():
#             queryset = queryset.filter(score__gte=int(min_score))
        
#         # Filter by maximum score
#         max_score = self.request.query_params.get('max_score')
#         if max_score and max_score.isdigit():
#             queryset = queryset.filter(score__lte=int(max_score))
        
#         # Filter by coin address
#         coin_address = self.request.query_params.get('coin')
#         if coin_address:
#             queryset = queryset.filter(coin__address__iexact=coin_address)
        
#         # Filter by coin symbol
#         coin_symbol = self.request.query_params.get('symbol')
#         if coin_symbol:
#             queryset = queryset.filter(coin__ticker__iexact=coin_symbol)
            
#         # Filter by developer address
#         developer = self.request.query_params.get('developer')
#         if developer:
#             queryset = queryset.filter(coin__creator__wallet_address__iexact=developer)
        
#         # Filter by minimum age
#         min_age = self.request.query_params.get('min_age_hours')
#         if min_age and min_age.isdigit():
#             queryset = queryset.filter(age_in_hours__gte=int(min_age))
        
#         # Filter non-rugged coins only
#         exclude_rugged = self.request.query_params.get('exclude_rugged')
#         if exclude_rugged and exclude_rugged.lower() == 'true':
#             queryset = queryset.filter(
#                 ~Q(coin__rug_flag__is_rugged=True)
#             )
        
#         return queryset
    
#     @action(detail=False, methods=['get'])
#     def top_coins(self, request):
#         """Returns top 10 coins by DRC score"""
#         top_coins = self.get_queryset().filter(
#             holders_count__gt=0,
#             ~Q(coin__rug_flag__is_rugged=True)
#         )[:10]
#         serializer = self.get_serializer(top_coins, many=True)
#         return Response(serializer.data)
    
#     @action(detail=False, methods=['get'])
#     def my_coins(self, request):
#         """Returns DRC scores for coins created by the authenticated user"""
#         user_coins = self.get_queryset().filter(coin__creator=request.user)
#         serializer = self.get_serializer(user_coins, many=True)
#         return Response(serializer.data)
    
#     @action(detail=True, methods=['post'])
#     def verify_contract(self, request, pk=None):
#         """Mark a coin's contract as verified"""
#         coin_drc = self.get_object()
        
#         # Check if user is the coin creator or an admin
#         if request.user != coin_drc.coin.creator and not request.user.is_staff:
#             return Response(
#                 {"detail": "You don't have permission to verify this contract"},
#                 status=status.HTTP_403_FORBIDDEN
#             )
        
#         coin_drc.verified_contract = True
#         coin_drc.save()
#         coin_drc.recalculate_score()
        
#         serializer = self.get_serializer(coin_drc)
#         return Response(serializer.data)
    
#     @action(detail=True, methods=['post'])
#     def update_audit(self, request, pk=None):
#         """Update audit status and score for a coin"""
#         coin_drc = self.get_object()
        
#         # Check if user is an admin (only admins can update audit status)
#         if not request.user.is_staff:
#             return Response(
#                 {"detail": "Only admins can update audit status"},
#                 status=status.HTTP_403_FORBIDDEN
#             )
        
#         # Get audit parameters from request
#         completed = request.data.get('completed', False)
#         score = request.data.get('score', 0)
        
#         try:
#             score = int(score)
#             if score < 0 or score > 100:
#                 return Response(
#                     {"detail": "Audit score must be between 0 and 100"},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
#         except ValueError:
#             return Response(
#                 {"detail": "Audit score must be an integer"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
            
#         # Update audit info
#         coin_drc.audit_completed = completed
#         coin_drc.audit_score = score
#         coin_drc.save()
#         coin_drc.recalculate_score()
        
#         serializer = self.get_serializer(coin_drc)
#         return Response(serializer.data)

class CoinRugFlagViewSet(viewsets.ModelViewSet): # fix this
    """API endpoint for viewing and updating coin rug flags"""
    queryset = CoinRugFlag.objects.all()
    serializer_class = CoinRugFlagSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by rugged status
        is_rugged = self.request.query_params.get('is_rugged')
        if is_rugged is not None:
            is_rugged_bool = is_rugged.lower() == 'true'
            queryset = queryset.filter(is_rugged=is_rugged_bool)
        
        # Filter by coin address
        coin_address = self.request.query_params.get('coin')
        if coin_address:
            queryset = queryset.filter(coin__address__iexact=coin_address)
        
        # Filter by developer
        developer = self.request.query_params.get('developer')
        if developer:
            queryset = queryset.filter(coin__creator__wallet_address__iexact=developer)
        
        return queryset
    
    def update(self, request, *args, **kwargs):
        """Only staff can update rug flags"""
        if not request.user.is_staff:
            return Response(
                {"detail": "Only staff members can update rug flags"},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
        
    def partial_update(self, request, *args, **kwargs):
        """Only staff can update rug flags"""
        if not request.user.is_staff:
            return Response(
                {"detail": "Only staff members can update rug flags"},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().partial_update(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def mark_rugged(self, request, pk=None):
        """Mark a coin as rugged with optional transaction ID and description"""
        rug_flag = self.get_object()
        
        # Check if user is staff
        if not request.user.is_staff:
            return Response(
                {"detail": "Only staff members can mark coins as rugged"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get parameters from request
        transaction_id = request.data.get('transaction_id')
        description = request.data.get('description', '')
        
        # Mark as rugged
        rug_flag.mark_as_rugged(transaction_id=transaction_id, description=description)
        
        serializer = self.get_serializer(rug_flag)
        return Response(serializer.data)